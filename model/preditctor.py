# -*- coding = utf-8 -*-
# @Time:
# @Author: GH
import os
import tensorflow as tf
from transformers import TFBertModel
# from transformers import AutoModel
from tensorflow_addons.text.crf import crf_decode
from untils.evaluate import entity_pos_extraction
from untils.PathManger import get_bert_path

class Predictor:
    def __init__(self, config, data_manger, model, checkpoint):
        self.babc_model = model
        self.checkpoint = checkpoint
        if config.bert_model_name == 'ethanyt/guwenbert-base':
            self.bert_model = TFBertModel.from_pretrained(get_bert_path())
        else:
            self.bert_model = TFBertModel.from_pretrained(config.bert_model_name)
        self.config = config
        self.data_manger = data_manger

    def predict(self, sentence):
        '''
        :param sentence: 预测的句子（str）
        :return: 预测的标签列表, 实体, 句子列表
        '''
        x, att_mask, y, sentence = self.data_manger.bert_embedding_sentence(sentence)

        inputs = self.bert_model(x, attention_mask=att_mask)[0]
        sentence_len = tf.math.count_nonzero(x, 1)
        logists, log_likehood, trainsition_param = self.babc_model(inputs=inputs, length=sentence_len, label=y)
        res = crf_decode(logists, trainsition_param, sentence_len)
        label_pre = res[0].numpy()
        sentence = sentence[0, 0:sentence_len[0]]
        pre_label = [str(self.data_manger.id2label[Id]) for Id in label_pre[0][0:sentence_len[0]]]
        pre_label = pre_label[1:-1]

        pos = []
        entity = []
        pos = entity_pos_extraction(''.join(pre_label), 0, pos)
        if pos is not None:
            entity = [(pre_label[start:end], start, end) for start, end in pos]
        return pre_label, entity, sentence


