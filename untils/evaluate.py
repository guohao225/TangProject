# -*- coding = utf-8 -*-
# @Time:
# @Author: GH
import re
import numpy
import pandas as pd
import tensorflow as tf
from seqeval import metrics as entity_metrics
from untils.DataManger import data_manger
from seqeval.metrics import f1_score, precision_score, recall_score, classification_report


def entity_pos_extraction(labels, l_end, location):
    match = re.compile(r'(B-LOC|B-PER|B-ORG)(I-PER|I-LOC|I-ORG)*')
    m = match.search(labels)
    try:
        pos = m.span()
        cur_label_start = l_end + pos[0]  # 计算标签在真实标签序列中的开始位置
        cur_label_end = cur_label_start + (pos[1] - pos[0]) / 5  # 计算标签在真实标签序列中的结束位置

        location.append((int(cur_label_start), int(cur_label_end)))

        # 递归执行
        entity_pos_extraction(labels[pos[1]:], cur_label_end, location)

        # 返回位置信息
        return location

    # 递归出口
    except AttributeError:
        return None

def evaluate(y, pre, config, data_man):
    if type(y) is not numpy.ndarray:
        y = y.numpy()
    if type(pre) is not numpy.ndarray:
        pre = pre.numpy()

    label_num = 0
    num_correct = 0

    pre_entity_correct = 0
    y_entitys = 0
    pre_entitys = 0

    accurcy = 0.0
    pre_acc = 0.0
    recall = 0.0
    f1 = 0.0

    for index in range(len(y)):
        pos_label_y = []
        pos_label_pre = []
        # 计算总的准确率
        y_pre = pd.DataFrame({'y': y[index], 'pre': pre[index]})
        y_pre = y_pre[y_pre['y'] != data_man.label2id[config.padding]]
        correct_label = len(y_pre[y_pre['y'] == y_pre['pre']])
        label_num += len(y_pre)
        num_correct += correct_label

        # 将标签id换成标签本身
        for i in range(len(y_pre)):
            y_pre.iloc[i, 0] = data_man.id2label[y_pre.iloc[i, 0]]
            y_pre.iloc[i, -1] = data_man.id2label[y_pre.iloc[i, -1]]

        y_pos = []
        pre_pos = []
        y_str = ''.join(y_pre['y'])
        y_str = y_str.replace("[PAD]", 'O')
        pre_str = ''.join(y_pre['pre'])
        pre_str = pre_str.replace("[PAD]", 'O')
        y_pos = entity_pos_extraction(y_str, 0, y_pos)
        pre_pos = entity_pos_extraction(pre_str, 0, pre_pos)

        if y_pos is not None:
            for start, end in y_pos:
                entity = y_pre.iloc[start:end, 0].to_list()
                if entity is not None:
                    pos_label_y.append((''.join(entity), start, end))
            y_entitys += len(pos_label_y)
        if pre_pos is not None:
            for start, end in pre_pos:
                entity = y_pre.iloc[start:end, -1].to_list()
                if entity is not None:
                    pos_label_pre.append((''.join(entity), start, end))
            pre_entitys += len(pos_label_pre)

        if y_pos is not None and pre_pos is not None:
            for i in range(len(pos_label_pre)):
                try:
                    pos_label_y.index(pos_label_pre[i])
                    pre_entity_correct += 1
                except ValueError:
                    continue

    # 计算准确率
    if num_correct != 0:
        accurcy = 1.0 * num_correct / label_num

    if pre_entity_correct != 0:
        # 计算预测准确率
        pre_acc = 1.0 * pre_entity_correct / pre_entitys

        # 计算召回率
        recall = 1.0 * pre_entity_correct / y_entitys

    # 计算f1
    if pre_acc > 0 and recall > 0:
        f1 = 2.0 * (pre_acc * recall) / (pre_acc + recall)

    return pre_acc, recall, f1

def restore_true_sentence_to_label(y_true, y_pre, id2label, decode=False):
    end_indices = numpy.argmax(y_true == 0, axis=1)
    y = []
    pre_y = []
    for i in range(y_true.shape[0]):
        if decode:
            y_sen = ["O" if j == 0 else id2label[j].decode() for j in
                     y_true[i, :end_indices[i] if end_indices[i] > 0 else -1]]
        else:
            y_sen = ["O" if j == 0 else id2label[j] for j in y_true[i, :end_indices[i] if end_indices[i] > 0 else -1]]
        y.append(y_sen)
        if decode:
            pre_y_len = ["O" if j == 0 else id2label[j].decode() for j in
                         y_pre[i, :end_indices[i] if end_indices[i] > 0 else -1]]
        else:
            pre_y_len = ["O" if j == 0 else id2label[j] for j in
                         y_pre[i, :end_indices[i] if end_indices[i] > 0 else -1]]
        pre_y.append(pre_y_len)
    return y, pre_y

def token_to_label(y_true, id2label):
    end_indices = numpy.argmax(y_true == 0, axis=1)
    y = []
    for i in range(y_true.shape[0]):
        y_sen = [id2label[j] for j in y_true[i, :end_indices[i]]]
        y.append(y_sen)
    return y

def metrics(y_true, y_pre, id2label, m=['precision']):
    if not isinstance(y_true, numpy.ndarray):
        y_true = y_true.numpy()
    if not isinstance(y_true, numpy.ndarray):
        y_pre = y_pre.numpy()
    y_vaild_true, y_pre_true = restore_true_sentence_to_label(y_true, y_pre, id2label)
    precision = 0,
    recall = 0,
    f1 = 0
    if 'precision' in m:
        precision = precision_score(y_vaild_true, y_pre_true)
    if 'recall' in m:
        recall = recall_score(y_vaild_true, y_pre_true)
    if 'f1' in m:
        f1 = f1_score(y_vaild_true, y_pre_true)
    if "report" in m:
        report = classification_report(y_vaild_true, y_pre_true, digits=2)
        print(report)
    return [precision, recall, f1]

def entity_level_f1(self, y_true, y_pred, digits=2, return_report=False, average="micro"):
    """
        entity-level-f1
        :params golden_tags Tags given manually
        :params predict_tags Prediction tags given by the model
        :return f1 score
    """
    assert len(y_true) == len(y_pred)
    score = entity_metrics.f1_score(y_true, y_pred, average=average)
    report = entity_metrics.classification_report(y_true, y_pred, digits=digits)
    self.logger.info(f"Classification report(Entity level):\n{report}")
    if return_report:
        return score, report
    return score

def extract_entities(tag_sequence, text, scores=None):
    entities = []
    current_entity = None
    start = None

    for i, tag in enumerate(tag_sequence):
        if tag.startswith('B-'):
            if current_entity is not None:
                if scores is not None:
                    entities.append((current_entity, text[start:i], start, i - 1, float(scores[i-1].numpy())))
                else:
                    entities.append((current_entity, text[start:i], start, i - 1))
            current_entity = tag[2:]
            start = i
        elif tag.startswith('I-'):
            if current_entity is None:
                continue
            if tag[2:] != current_entity:
                if scores is not None:
                    entities.append((current_entity, text[start:i], start, i - 1, float(scores[i-1].numpy())))
                else:
                    entities.append((current_entity, text[start:i], start, i - 1))
                current_entity = None
                start = None
        elif tag == 'O':
            if current_entity is not None:
                if scores is not None:
                    entities.append((current_entity, text[start:i], start, i - 1, float(scores[i-1].numpy())))
                else:
                    entities.append((current_entity, text[start:i], start, i - 1))
                current_entity = None
                start = None

    if current_entity is not None:
        entities.append((current_entity, text[start:len(tag_sequence)], start, len(tag_sequence) - 1, float(scores[len(tag_sequence) - 1].numpy())))

    return entities

def get_tag_score(sequence):
    # 沿着最后一维计算张量的最大值
    max_values = tf.reduce_max(sequence, axis=-1)
    # 移除张量的最后一维，得到形状为 (3, 5) 的结果
    max_values = tf.squeeze(max_values)
    return max_values

def get_real_logist(logist, lens):
    examples = []
    lens = [x if x < 200 else 200 for x in lens]
    for i in range(len(lens)):
        if len(logist.shape) == 2:
            example = logist[i, :lens[i]]
        else:
            example = logist[i, :lens[i], :]
        examples.append(example)
    return examples


##计算指标
def compute_f1(y_true, y_pred):
    score = tf.numpy_function(compute_metrics, [y_true, y_pred], tf.float32)
    return score

def compute_metrics(y_true, y_pred):
    y_true, y_pred = restore_true_sentence_to_label(y_true, y_pred, data_manger.id2label)
    print(y_true, y_pred)
    f1 = f1_score(y_true, y_pred, average='macro')
    f1 = tf.convert_to_tensor(f1, dtype=tf.float32)
    return f1