# @time:2023/9/4 10:17
# @functional:
import os
os.environ['TF_KERAS'] = '1'
os.environ["CUDA_VISIBLE_DEVICES"] = "0"

import Metrics
from Metrics import PrecisionMetrics, RecallMetrics, F1Metrics
import data_util as du
from model import REModel, ModelCallback
from model_config import CONFIG
import tensorflow as tf
# from tensorflow.keras.optimizers import Adam, SGD
from bert4keras.optimizers import Adam
from tensorflow.keras.losses import SparseCategoricalCrossentropy
from tensorflow.keras.utils import to_categorical
import numpy as np
from sklearn.metrics import classification_report

# 设置显存自动增长
gpus = tf.config.experimental.list_physical_devices('GPU')
if gpus:
    try:
        for gpu in gpus:
            tf.config.experimental.set_memory_growth(gpu, True)
    except RuntimeError as e:
        print(e)



seed = 42
tf.random.set_seed(42)
os.environ["PYTHONHASHSEED"] = str(seed)
Metrics.AVER = 'micro'


data_loader = du.DataLoader(max_len=CONFIG.max_len, segment=False)
remodel = REModel(vocab_size=data_loader.get_vocab_size(), seed=seed, embed_dim=CONFIG.embedding_dim)
callback = ModelCallback()
dev_rate = 0.2

def expand_dim(x1, x2, x3, x4):
    x1 = tf.expand_dims(x1, axis=-1)
    x2 = tf.expand_dims(x2, axis=-1)
    x3 = tf.expand_dims(x3, axis=-1)
    x4 = tf.expand_dims(x4, axis=-1)
    x1 = np.pad(x1, [(0, 0), (0, 0), (0, 4)], mode='constant')
    x2 = np.pad(x2, [(0, 0), (0, 0), (0, 4)], mode='constant')
    x3 = np.pad(x3, [(0, 0), (0, 0), (0, 4)], mode='constant')
    x4 = np.pad(x4, [(0, 0), (0, 0), (0, 4)], mode='constant')
    return x1, x2, x3, x4

#
if CONFIG.use_seg:
    sample_tokens_id, seg_ids, e1_mask_list, tags, e1_pos, e2_pos, seg= data_loader.load_train_data2('train_file')
    val_tokens_id, val_seg_ids, val_e1, val_tags, val_re1, val_re2, val_seg = data_loader.load_train_data2('val_file')
    sample_tokens_id, e1_mask_list, e1_pos, e2_pos = expand_dim(sample_tokens_id, e1_mask_list, e1_pos, e2_pos)
    val_tokens_id, val_e1, val_re1, val_re2 = expand_dim(val_tokens_id, val_e1, val_re1, val_re2)
    x_train = np.stack((sample_tokens_id, e1_mask_list, e1_pos, e2_pos, seg), axis=-1)
    x_val = np.stack((val_tokens_id, val_e1, val_re1, val_re2, val_seg), axis=-1)
else:
    sample_tokens_id, seg_ids, e1_mask_list, tags, e1_pos, e2_pos , (en1, en1_ids), (en2, en2_ids) \
        = data_loader.load_train_data2('train_file')
    val_tokens_id, val_seg_ids, val_e1, val_tags, val_re1, val_re2 ,(val_en1, val_en1_ids), (val_en2, val_en2_ids)\
        = data_loader.load_train_data2('val_file')
    t_tokens_id, t_seg_ids, t_e1, t_tags, t_re1, t_re2, (t_en1, t_en1_ids), (t_en2, t_en2_ids)\
        = data_loader.load_train_data2('test_file')
    x_train = np.stack((sample_tokens_id, seg_ids, e1_mask_list, e1_pos, e2_pos, en1, en1_ids, en2, en2_ids), axis=-1)
    x_val = np.stack((val_tokens_id, val_seg_ids, val_e1, val_re1, val_re2, val_en1, val_en1_ids, val_en2, val_en2_ids), axis=-1)
    x_test = np.stack((t_tokens_id, t_seg_ids, t_e1, t_re1, t_re2, t_en1, t_en1_ids, t_en2, t_en2_ids), axis=-1)
remodel.compile(optimizer=Adam(learning_rate=CONFIG.learn_rate),
                loss=SparseCategoricalCrossentropy(),
                metrics=['accuracy', PrecisionMetrics(), RecallMetrics(), F1Metrics()],
                # metrics=[PrecisionMetrics(), RecallMetrics(), F1Metrics()]
                )
remodel.fit(x_train, tags, batch_size=CONFIG.batch_size, validation_data=(x_val, val_tags), epochs=CONFIG.epochs, shuffle=False, callbacks=callback)

remodel.load_weights(CONFIG.save_path)
remodel.evaluate(x_test, t_tags)
# pre = remodel.predict(x_test)
# print(classification_report(t_tags, tf.argmax(pre, axis=-1), digits=4))
# remodel.evaluate(x_val, val_tags)


