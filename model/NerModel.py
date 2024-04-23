import tensorflow as tf
import bert4keras.models as b4k
from tensorflow.keras import layers
import numpy as np
from keras_self_attention import SeqSelfAttention
from model.Recorder import recorder
from CRFLAYER import CRF
import untils.evaluate as eva
from untils.evaluate import restore_true_sentence_to_label
from bert4keras.layers import Dropout, Bidirectional, LSTM, Dense
from tensorflow.keras.initializers import glorot_normal, glorot_uniform, orthogonal
from tensorflow.keras import Model
from seqeval.metrics import f1_score, recall_score, precision_score
from untils.DataManger import data_manger
from untils.Config import CONFIG
import keras.backend as K
from tensorflow.python.ops import array_ops
import untils.tf_util as tf_utils
tf.random.set_seed(CONFIG.seed)

class NerModel(Model):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if CONFIG.use_bert:
            self.bert = b4k.build_transformer_model('./checkpoints/MiniRBT-h256-pt/bert_config.json',
                                                    "./checkpoints/MiniRBT-h256-pt/bert_model.ckpt",
                                                    return_keras_model=True)
        else:
            self.bert = layers.Embedding(data_manger.vocab_len,
                                         CONFIG.embedding_dim,
                                         embeddings_initializer=glorot_normal(seed=CONFIG.seed),
                                         mask_zero=True
                                         )
        if CONFIG.use_seg:
            self.seg_Embeeding = layers.LSTM(100, return_sequences=True)
        if CONFIG.ver_model == -1:
            self.bilstm = layers.Bidirectional(AttentionLSTM(CONFIG.hidden_dim,
                                                             CONFIG.attention_dim,
                                                             return_sequences=True,
                                                             kernel_initializer=glorot_uniform(seed=CONFIG.seed),
                                                             recurrent_initializer=orthogonal(seed=CONFIG.seed)
                                                             ))
        else:
            self.bilstm = Bidirectional(LSTM(CONFIG.hidden_dim,
                                             return_sequences=True,
                                             kernel_initializer=glorot_uniform(seed=CONFIG.seed),
                                             recurrent_initializer=orthogonal(seed=CONFIG.seed)
                                             ))
        #
        if CONFIG.use_cnn:
            self.cnn = layers.Conv1D(CONFIG.cnn_filters,
                                     kernel_size=CONFIG.kernel_size,
                                     padding='same',
                                     activation='tanh',
                                     kernel_initializer=glorot_uniform(seed=CONFIG.seed))
        self.max_pool = layers.MaxPooling1D(padding='same',
                                            strides=1,
                                            pool_size=3)

        if CONFIG.use_crf:
            self.crf = CRF(len(data_manger.id2label), chain_initializer=glorot_normal(seed=CONFIG.seed))
        else:
            self.crf = Dense(len(data_manger.id2label), activation='softmax', kernel_initializer=glorot_uniform(seed=CONFIG.seed))

        self.dropout = Dropout(CONFIG.droupout, seed=CONFIG.seed)

    def call(self, inputs, training=False):
        x, mask, seg_tokens = tf.split(inputs, 3, axis=-1)
        x = tf.reduce_sum(x, axis=-1)
        mask = tf.reduce_sum(mask, axis=-1)
        seg_tokens = tf.cast(seg_tokens, dtype=tf.float32)
        if CONFIG.use_bert:
            context = self.bert([x, mask])
        else:
            context = self.bert(x)
        if CONFIG.use_seg:
            seg_context = self.seg_Embeeding(seg_tokens)
            context = tf.concat([context, seg_context], axis=-1)
        context = self.dropout(context, training=training)
        if CONFIG.use_cnn:
            local = self.cnn(context, training=training)
            local = self.max_pool(local, training=training)
            context = tf.concat([local, context], axis=-1)

        timecontext = self.bilstm(context, training=training)

        if CONFIG.use_crf:
            decoded_sequence, potentials, sequence_length, chain_kernel = self.crf(timecontext, training=training)
        else:
            potentials = self.crf(timecontext, training=training)
            decoded_sequence = tf.argmax(potentials, -1)
            sequence_length = []
            chain_kernel = []
        return decoded_sequence, potentials, sequence_length, chain_kernel

    def train_step(self, data):
        x, y = data
        with tf.GradientTape() as tape:
            decoded_sequence, potentials, sequence_length, chain_kernel = self(x, training=True)
            loss = self.compiled_loss(y, potentials)
        gradients = tape.gradient(loss, self.trainable_variables)
        self.compiled_metrics.update_state(y, decoded_sequence)
        self.optimizer.apply_gradients(zip(gradients, self.trainable_variables))
        return {m.name: m.result() for m in self.metrics}

    def test_step(self, data):
        x, y = data
        decoded_sequence, potentials, sequence_length, chain_kernel = self(x)
        loss = self.compiled_loss(y, potentials)
        self.compiled_metrics.update_state(y, decoded_sequence)
        return {m.name: m.result() for m in self.metrics}

    def predict_user(self, sentences):
        sequence, lens, _2 = data_manger.bert_embedding_sentences(sentences)
        decoded_sequence, logists, _, chain = self.call(sequence, training=False)
        tag_seq = self.get_tag_seq(decoded_sequence, logists=False)
        for i in range(0, len(tag_seq)):
            tag_seq[i] = ["O" if item == '[PAD]' else item for item in tag_seq[i]]
        entitys = self.extract_entities_without_score(tag_seq)
        return tag_seq, entitys

    @classmethod
    def get_tag_seq(cls, sequence, logists=True):
        tag_seqs = []
        for item in sequence:
            if logists:
                item = tf.argmax(item, axis=-1).numpy()
            tag_seq = [data_manger.id2label[id] if id != 0 else 'O' for id in item]
            tag_seqs.append(tag_seq)
        return tag_seqs

    @classmethod
    def extract_entities(cls, sequence, scores, content):
        seq_entitys = []
        for item, score, text in zip(sequence, scores, content):
            entitys = eva.extract_entities(item, text, score)
            seq_entitys.append(entitys)
        return seq_entitys

    @classmethod
    def extract_entities_without_score(cls, sequence):
        seq_entitys = []
        for item in sequence:
            entitys = eva.extract_entities(item)
            seq_entitys.append(entitys)
        return seq_entitys


class AttentionLSTM(layers.LSTM):
    def __init__(self, units, atn_units, **kwargs):
        super(AttentionLSTM, self).__init__(units, **kwargs)
        self.atn_units = atn_units
        self.dropout_lay = Dropout(0.5, seed=CONFIG.seed)
        self.attention = SeqSelfAttention(units=CONFIG.attention_dim,
                                          attention_width=CONFIG.attention_width,
                                          kernel_initializer=glorot_normal(seed=CONFIG.seed),
                                          attention_regularizer_weight=CONFIG.attention_regularizer_weight,
                                          attention_activation='tanh'
                                          )

    def call(self, inputs, training=False):
        lstm_outputs = super(AttentionLSTM, self).call(inputs, training=training)
        lstm_att = self.attention(lstm_outputs, training=training)
        lstm_att = self.dropout_lay(lstm_att, training=training)
        outputs = tf.concat([lstm_att, lstm_outputs], axis=-1)
        return outputs

    # 将自定义的属性加入到LSTM中（重写get_config方法）
    def get_config(self):
        base_config = super(AttentionLSTM, self).get_config()
        config = {'atn_units': self.atn_units}
        return dict(list(base_config.items()) + list(config.items()))


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
    y_true, y_pred = restore_true_sentence_to_label(y_true, y_pred, data_manger.id2label, decode=False)
    metrics = 0
    if name == b'precision':
        metrics = precision_score(y_true, y_pred, average=average)
    elif name == b'recall':
        metrics = recall_score(y_true, y_pred, average=average)
    elif name == b'f1':
        metrics = f1_score(y_true, y_pred, average=average)
    metrics = tf.convert_to_tensor(metrics, dtype=tf.float32)
    return metrics


class AtnCallback(tf.keras.callbacks.Callback):
    def __init__(self, save_model=True, is_record=False, save_dir=CONFIG.save_path):
        super(AtnCallback, self).__init__()
        self.best_f1 = 0
        self.min_loss = 100
        self.save_dir = save_dir

    def on_epoch_end(self, epoch, logs=None):
        if CONFIG.mode == 1:
            recorder.set_train_status({'loop': epoch, 'score': logs['val_f1'], 'loss': logs['loss']})
        # if self.min_loss > logs['loss']:
        #     self.min_loss = logs['loss']
        #     print("\033[0;31;40m*****************|saving model weight....|************************\033[0m")
        #     self.model.save_weights(f'{CONFIG.checkpoints_dir}/{self.save_dir}')
        if logs['val_f1'] > self.best_f1 and CONFIG.save_model:
            self.best_f1 = logs['val_f1']
            print("\033[0;31;40m*****************|saving model weight....|************************\033[0m")
            self.model.save_weights(f'{CONFIG.checkpoints_dir}/{self.save_dir}')


