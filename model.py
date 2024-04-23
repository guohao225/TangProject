# @time:2023/9/3 23:50
# @functional:
import math
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
from tensorflow.keras.initializers import glorot_normal, orthogonal, glorot_uniform
from keras_pos_embd import PositionEmbedding
from model_config import CONFIG
import keras.backend as K
import bert4keras.models as tool
import tf_util as tf_utils
from tensorflow.python.ops import array_ops
from bert4keras.layers import GlobalPointer, MultiHeadAttention
from tensorflow.keras.layers import Attention

class REModel(keras.Model):
    def __init__(self, vocab_size, seed=CONFIG.seed,
                 embed_dim=CONFIG.embedding_dim,
                 pos_embed=CONFIG.position_dim,
                 hidden_dim=CONFIG.hidden_dim,
                 use_bert=CONFIG.use_bert,
                 use_cnn=False):
        super(REModel, self).__init__()
        self.hidden_dim = hidden_dim
        if CONFIG.use_capsule:
            pass
        else:
            self.dense = layers.Dense(CONFIG.num_class, activation='softmax', kernel_initializer=glorot_normal(seed))
        if CONFIG.use_cnn:
            self.cnn = layers.Conv1D(300, kernel_size=3, padding='same', activation='tanh')
        if CONFIG.use_bicnn:
            self.atn_lstm = layers.Bidirectional(AttentionLSTM(hidden_dim,
                                                               embed_dim + pos_embed,
                                                               # 100,
                                                               kernel_initializer=glorot_normal(seed=seed),
                                                               recurrent_initializer=orthogonal(seed=seed),
                                                               return_sequences=False,
                                                               dropout=0.5))
        else:
            self.atn_lstm = layers.Bidirectional(layers.LSTM(hidden_dim,
                                                             kernel_initializer=glorot_normal(seed=seed),
                                                             recurrent_initializer=orthogonal(seed=seed),
                                                             dropout=0.5))
        self.dropout = layers.Dropout(CONFIG.dropout, seed=seed)
        if use_bert:
            self.word_embed = tool.build_transformer_model('./tiny_bert/guwen_bert/bert_config.json',
                                                           checkpoint_path='./tiny_bert/guwen_bert/bert_model.ckpt',
                                                           return_keras_model=True)
        else:
            self.word_embed = layers.Embedding(vocab_size,
                                               embed_dim,
                                               mask_zero=True,
                                               embeddings_initializer=glorot_uniform(seed=seed))
        # if CONFIG.use_seg:
        # self.seg_embed = layers.Conv1D(100, padding='same', kernel_size=2, kernel_initializer=glorot_normal(seed=seed))
        self.pos_embed_size = pos_embed
        self.pos_embd = PositionEmbedding(input_dim=CONFIG.max_len+2, output_dim=pos_embed,
                                          mode=PositionEmbedding.MODE_EXPAND, embeddings_initializer=glorot_uniform(seed=seed))
        self.pos1_embd = PositionEmbedding(input_dim=CONFIG.max_len, output_dim=pos_embed,
                                           mode=PositionEmbedding.MODE_EXPAND, embeddings_initializer=glorot_uniform(seed=seed))
        self.pos2_embd = PositionEmbedding(input_dim=CONFIG.max_len, output_dim=pos_embed,
                                           mode=PositionEmbedding.MODE_EXPAND, embeddings_initializer=glorot_uniform(seed=seed))
        self.add = layers.Add()
        self.attention = layers.AdditiveAttention(use_scale=False)

    def call(self, inputs, training=True):
        posembed = None
        if CONFIG.use_seg:
            split_tensors = tf.split(inputs, num_or_size_splits=5, axis=-1)
            split_tensors_as_2d = [tf.squeeze(split_tensor, axis=-1) for split_tensor in split_tensors]
            token_id, pos1, re_pos1, re_pos2, seg = split_tensors_as_2d
            token_id = tf.reduce_sum(token_id, axis=-1)
            pos1 = tf.reduce_sum(pos1, axis=-1)
            re_pos1 = tf.reduce_sum(re_pos1, axis=-1)
            re_pos2 = tf.reduce_sum(re_pos2, axis=-1)
            output = self.word_embed(token_id, training=training)
            #将seg的类型转化为flot32
            seg = tf.cast(seg, tf.float32)
            seg_output = self.seg_embed(seg)
            output = tf.concat([output, seg_output], axis=-1)
        else:
            split_tensors = tf.split(inputs, num_or_size_splits=9, axis=2)
            split_tensors_as_2d = [tf.squeeze(split_tensor, axis=2) for split_tensor in split_tensors]
            token_id, seg_ids, pos1, re_pos1, re_pos2, en1, en1_ids, en2, en2_ids = split_tensors_as_2d
            ## 字符嵌入
            if CONFIG.use_bert:
                output = self.word_embed([token_id, seg_ids])
            else:
                output = self.word_embed(token_id, training=training)

        ##实体信息
        if CONFIG.use_entity_info:
            entity_w1 = self.entity_average(output, en1, en1_ids, training)
            entity_w2 = self.entity_average(output, en2, en2_ids, training)
            entity_wieght = self.add([entity_w1, entity_w2])
            output =self.add([output, entity_wieght])

        ## 相对位置信息
        if CONFIG.use_re_pos:
            pos1_embed = self.pos1_embd(re_pos1, training=training)
            pos2_embed = self.pos2_embd(re_pos2, training=training)
            posembed = self.add([pos1_embed, pos2_embed])
            ## 位置嵌入
        if CONFIG.use_ab_pos:
            ab_pos_embed = self.pos_embd(pos1, training=training)
            if posembed is not None:
                posembed = posembed+ab_pos_embed
            else:
                posembed = ab_pos_embed
            # output = self.add([output, ab_pos_embed])
            # if CONFIG.use_re_pos:
            #     posembed = tf.multiply(posembed, ab_pos_embed)
            # else:
            #     posembed = ab_pos_embed
        if posembed is not None:
            concat_hidden = tf.concat([output, posembed], axis=-1)
        else:
            concat_hidden = output

        if CONFIG.use_cnn:
            concat_hidden = self.cnn(concat_hidden, training=training)

        concat_hidden = self.dropout(concat_hidden, training=training)
        lstm_out = self.atn_lstm(concat_hidden, training=training)
        logists = self.dense(lstm_out, training=training)
        return logists

    @tf.function
    def entity_average(self, word_vec, entity_token, entity_ids, training):
        if CONFIG.use_bert:
            entity_vec = self.word_embed([entity_token, entity_ids])
        else:
            entity_vec = self.word_embed(entity_token)
        q = entity_vec
        v = word_vec
        k = word_vec
        scores = tf.matmul(q, k, transpose_b=True)
        weights = tf.nn.softmax(scores)

        def dropped_weights():
            return tf.nn.dropout(weights, rate=0.5)

        weights = tf_utils.smart_cond(
                K.learning_phase(),
                dropped_weights,
                lambda: array_ops.identity(weights))
        result = tf.matmul(weights, v)
        return result



    def train_step(self, data):
        x, y = data
        with tf.GradientTape() as tape:
            logits = self(x)
            loss = self.compiled_loss(y, logits)
        self.compiled_metrics.update_state(y, logits)
        gradients = tape.gradient(loss, self.trainable_variables)
        self.optimizer.apply_gradients(zip(gradients, self.trainable_variables))
        return {m.name: m.result() for m in self.metrics}

    def test_step(self, data):
        x, y = data
        logits = self(x, training=False)
        self.compiled_loss(y, logits)
        self.compiled_metrics.update_state(y, logits)
        return {m.name: m.result() for m in self.metrics}

class AttentionLSTM(layers.LSTM):
    def __init__(self, units, cnn_units=None, **kwargs):
        self.cnn_units = cnn_units
        self.dropout_lay = layers.Dropout(CONFIG.dropout, seed=CONFIG.seed)
        self.cnn_lay = layers.Conv1D(self.cnn_units,
                                     kernel_size=CONFIG.cnn_kernel_size,
                                     padding='same',
                                     kernel_initializer=glorot_uniform(seed=CONFIG.seed),
                                     activation=CONFIG.cnn_act,
                                     )
        self.max_pool_lay = layers.MaxPooling1D(padding='same',
                                                pool_size=CONFIG.max_pooling_size,
                                                strides=2
                                                )
        super(AttentionLSTM, self).__init__(units=units, **kwargs)


    def call(self, inputs, training=True):
        cnn_out = self.cnn_lay(inputs, training=training)
        cnn_out = self.max_pool_lay(cnn_out, training=training)
        cnn_out = self.dropout_lay(cnn_out, training=training)
        outputs = super(AttentionLSTM, self).call(cnn_out, training=training)
        return outputs

    def get_config(self):
        base_config = super(AttentionLSTM, self).get_config()
        config = {'cnn_units': self.cnn_units}
        return dict(list(base_config.items()) + list(config.items()))




class ModelCallback(tf.keras.callbacks.Callback):
    def __init__(self, save_model=True):
        super(ModelCallback, self).__init__()
        self.save_model = save_model
        self.max_f1 = 0
        self.miss = 0

    def on_epoch_end(self, epoch, logs=None):
        f1 = logs['val_f1']
        if f1 > self.max_f1:
            self.max_f1 = f1
            self.model.save_weights(CONFIG.save_path)
        else:
            self.miss += 1
        if self.miss > 15:
            if CONFIG.auto_stop_tran:
                self.model.stop_training = True



