# -*- coding = utf-8 -*-
# @Time:
# @Author: GH
from tensorflow.keras.optimizers import Adam, Adagrad, SGD, Nadam
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers, Model
from keras_self_attention import SeqSelfAttention
from keras_multi_head import MultiHeadAttention
from CRFLAYER import CRF
from seqeval.metrics import precision_score, recall_score, f1_score
from tensorflow.keras.regularizers import l2
import untils.evaluate as eva
from model.Recorder import recorder

id2label = ['[PAD]', 'O', 'B-PER', 'B-LOC', 'B-ORG', 'I-PER', 'I-LOC', 'I-ORG']


class BABCModel(keras.Model):
    def __init__(self, config, label_num, data_man=None, **kwargs):
        super(BABCModel, self).__init__(**kwargs)
        self.data_man = data_man
        self.config = config
        if config.ver_model == -1:
            self.atn_bilstm = layers.Bidirectional(AttentionLSTM(
                units=config.hidden_dim,
                atn_units=config.attention_dim,
                b_atten=config.b_attention,
                atn_type=config.attention_type,
                multi_head_num=config.multi_head_num,
                return_sequences=True,
                dropout = 0.5
            ))
        elif config.ver_model == 1:
            self.atn_bilstm = layers.LSTM(units=config.hidden_dim, return_sequences=True,
                                          kernel_regularizer=l2(self.config.regularizers_coeffiicient))
        else:
            self.atn_bilstm = layers.Bidirectional(layers.LSTM(units=config.hidden_dim,
                                                               return_sequences=True))
        self.dropout_ly = layers.Dropout(0.5,seed=30)
        self.use_bert = config.use_bert
        self.cnn= layers.Conv1D(300, kernel_size=1, padding="same")
        if not self.use_bert and not config.use_pre_embedding:
            self.embedding = layers.Embedding(data_man.vocab_len, config.embedding_dim, mask_zero=True)
        if config.use_crf:
            self.crf = CRF(label_num, use_boundary=False)
        else:
            self.crf = layers.Dense(units=label_num, activation="softmax")

    def call(self, inputs, training=True):
        if self.use_bert or self.config.use_pre_embedding:
            inputs_embedding = self.bert(inputs)[0]
        else:
            inputs_embedding = self.embedding(inputs)
        cnn_out = self.cnn(inputs_embedding)
        inputs_embedding = tf.add(cnn_out, inputs_embedding)
        inputs_embedding = self.dropout_ly(inputs_embedding, training=training)
        outputs = self.atn_bilstm(inputs_embedding, training=training)
        if self.config.use_crf:
            decoded_sequence, potentials, sequence_length, chain_kernel = self.crf(outputs)
        else:
            outputs = self.crf(outputs)
            decoded_sequence = tf.argmax(outputs, -1)
            potentials = outputs
            sequence_length = []
            chain_kernel = []
        return decoded_sequence, potentials, sequence_length, chain_kernel

    def train_step(self, data):
        x, y = data
        with tf.GradientTape() as tape:
            decoded_sequence, potentials, sequence_length, chain_kernel = self(x)
            loss = self.compiled_loss(y, potentials)
        self.compiled_metrics.update_state(y, decoded_sequence)
        gradients = tape.gradient(loss, self.trainable_variables)
        self.optimizer.apply_gradients(zip(gradients, self.trainable_variables))
        return {m.name: m.result() for m in self.metrics}

    def test_step(self, data):
        x, y = data
        decoded_sequence, potentials, sequence_length, chain_kernel = self(x, training=False)
        loss = self.compiled_loss(y, potentials)
        self.compiled_metrics.update_state(y, decoded_sequence)
        return {m.name: m.result() for m in self.metrics}

    @classmethod
    def get_tag_seq(cls, sequence):
        tag_seqs = []
        for item in sequence:
            item = tf.argmax(item, axis=-1).numpy()
            tag_seq = [id2label[id] for id in item]
            tag_seqs.append(tag_seq)
        return tag_seqs

    @classmethod
    def extract_entities(cls, sequence, scores):
        seq_entitys = []
        for item, score in zip(sequence, scores):
            entitys = eva.extract_entities(item, score)
            seq_entitys.append(entitys)
        return seq_entitys

    def loss(self, y_true, y_pre):
        tf.nn.sparse_softmax_cross_entropy_with_logits


##bilistm Embedding Attention
class AttentionLSTM(layers.LSTM):
    def __init__(self, units, atn_units, b_atten, atn_type, multi_head_num=3, **kwargs):
        super(AttentionLSTM, self).__init__(units, **kwargs)
        self.atn_units = atn_units
        self.b_atten = b_atten
        self.atn_type = atn_type
        self.multi_head_num = multi_head_num
        self.dropout_lay = layers.Dropout(0.5, seed=30)
        if self.atn_type == 0:
            self.attention = layers.AdditiveAttention(use_scale=True, causal=True)
        if self.atn_type == 1:
            self.attention = SeqSelfAttention(units=atn_units,
                                              attention_width=5,
                                              use_attention_bias=False,
                                              use_additive_bias=False)
        if self.atn_type == 2:
            self.attention = SeqSelfAttention(units=atn_units,
                                              attention_type=SeqSelfAttention.ATTENTION_TYPE_MUL
                                              )
        elif self.atn_type == 3:
            self.attention = MultiHeadAttention(head_num=self.multi_head_num, name="Multi-Head")

    def call(self, inputs, training=True):
        lstm_outputs = super(AttentionLSTM, self).call(inputs, training=training)
        lstm_att = self.attention(lstm_outputs, training=training)
        outputs = tf.concat([lstm_outputs, lstm_att], axis=-1)
        outputs = self.dropout_lay(outputs, training=training)
        return outputs

    # 将自定义的属性加入到LSTM中（重写get_config方法）
    def get_config(self):
        base_config = super(AttentionLSTM, self).get_config()
        config = {'atn_units': self.atn_units,
                    'b_atten': self.b_atten,
                    'atn_type': self.atn_type,
                    'multi_head_num': self.multi_head_num
                }
        return dict(list(base_config.items()) + list(config.items()))

## 每个epoch的回调类
class AtnCallback(tf.keras.callbacks.Callback):
    def __init__(self, save_model=True, score_name='f1', is_record=True, save_dir="MRSA/MRSA", min_stop_loss=0.05):
        super(AtnCallback, self).__init__()
        self.miss = 0
        self.best_f1 = 0
        self.save_model = save_model
        self.score_name = score_name
        self.is_record = is_record
        self.save_path = save_dir
        self.min_loss = min_stop_loss
        self.lower_loss = 0


    def on_epoch_end(self, epoch, logs=None):
        if self.is_record:
            recorder.set_train_status({'epoch': epoch, 'score': logs[f'{self.score_name}'], 'loss': logs['loss']})
        if logs[f'val_{self.score_name}'] > self.best_f1:
            if self.save_model:
                dir = self.model.config.checkpoints_dir
                self.model.save_weights(f'{dir}/${self.save_path}')
            self.best_f1 = logs[f'val_{self.score_name}']
            self.miss = 0
        if logs['loss'] < self.min_loss:
            self.model.stop_training = True
# 计算指标
class NERMetrics(tf.keras.metrics.Metric):
    def __init__(self, name='precision', average='micro', **kwargs):
        super(NERMetrics, self).__init__(name=name, **kwargs)
        self.score = self.add_weight(name='score', initializer='zeros')
        self.total = self.add_weight(name='total', initializer='zeros')
        self.metrics_type = name
        self.average = average

    def update_state(self, y_true, y_pre, sample_weight=None):
        score = tf.numpy_function(compute_metrics, [y_true, y_pre, self.metrics_type], tf.float32)
        self.score.assign_add(score)
        self.total.assign_add(1.)

    def result(self):
        return self.score / self.total

    def reset_state(self):
        self.score.assign(0)
        self.total.assign(0)
def compute_metrics(y_true, y_pred, name='precision', average='macro'):
    y_true, y_pred = eva.restore_true_sentence_to_label(y_true, y_pred, id2label, decode=False)
    metrics = 0
    if name == b'precision':
        metrics = precision_score(y_true, y_pred, average=average)
    elif name == b'recall':
        metrics = recall_score(y_true, y_pred, average=average)
    elif name == b'f1':
        metrics = f1_score(y_true, y_pred, average=average)
    metrics = tf.convert_to_tensor(metrics, dtype=tf.float32)
    return metrics
## 将解码序列还原成原始句子的长度以及句子对应的标签序列
def convert_tensor_to_true_length(tensor_true, tensor_pre=None):
    lengths = tf.reduce_sum(tf.cast(tensor_true != 0, tf.int32), axis=1)
    y = tf.zeros(tf.reduce_sum(lengths))
    y_pre = tf.zeros(tf.reduce_sum(lengths))
    start = 0
    for i in range(tensor_true.shape[0]):
        y[start:start + lengths[i]] = tensor_true[i, :lengths[i]]
        if tensor_pre is not None:
            y_pre[start:start + lengths[i]] = tensor_pre[i, :lengths[i]]
        start += lengths[i]
    return y, y_pre




