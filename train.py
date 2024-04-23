# @time:2023/3/11 14:10
# @functional:
import os.path

import pandas
import os
os.environ['TF_KERAS'] = '1'

import tensorflow as tf
from untils.Config import CONFIG
os.environ["CUDA_VISIBLE_DEVICES"] = "0"
# 设置显存自动增长
gpus = tf.config.experimental.list_physical_devices('GPU')
if gpus:
    try:
        for gpu in gpus:
            tf.config.experimental.set_memory_growth(gpu, True)
    except RuntimeError as e:
        print(e)

tf.random.set_seed(CONFIG.seed)
os.environ["PYTHONHASHSEED"] = str(CONFIG.seed)

import numpy as np
from tensorflow.keras.optimizers import Adam
from model.NerModel import NerModel, NERMetrics, AtnCallback
from untils.DataManger import data_manger
from keras.losses import SparseCategoricalCrossentropy
from untils.evaluate import metrics, restore_true_sentence_to_label
from seqeval.metrics import classification_report


def train_fit():
    x, x_ver, y, y_ver, mask, mask_ver, sequence_len, sequence_len_ver, seg, seg_ver = data_manger.bert_embedding_from_file(CONFIG.train_file_name, return_ver=True)
    # x_ver, y_ver, mask_ver, sequence_len_ver, seg_ver = data_manger.bert_embedding_from_file(CONFIG.ver_file_name)
    model = NerModel()
    cbk = AtnCallback()
    x = data_manger.expand_dim(x)
    mask = data_manger.expand_dim(mask)
    x = np.concatenate((x, mask, seg), axis=-1)
    x_ver = data_manger.expand_dim(x_ver)
    mask_ver = data_manger.expand_dim(mask_ver)
    x_ver = np.concatenate((x_ver, mask_ver, seg_ver), axis=-1)
    model.compile(optimizer=Adam(learning_rate=CONFIG.learning_rate), loss=SparseCategoricalCrossentropy(),
                  metrics=[NERMetrics(name='precision'), NERMetrics(name='recall'), NERMetrics(name='f1')])
    his = model.fit(x, y, batch_size=64, epochs=20, shuffle=False, validation_data=(x_ver, y_ver), callbacks=cbk)
    model.load_weights("./checkpoints/POEM/POEM")
    pre = model.predict(x_ver)[0]
    # print(pre)
    y_true, y_pred = restore_true_sentence_to_label(y_ver, pre, data_manger.id2label, decode=False)
    print(classification_report(y_true, y_pred, digits=4))
    # metrics(y_ver, pre, data_manger.id2label, ['report'])

train_fit()