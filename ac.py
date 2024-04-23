import os

from activteLearner import ActiveLearning, DataPool
import tensorflow as tf
from untils import DataBase as db
import untils.evaluate as eva
from untils.Config import Config
from untils.DataManger import DataManger
from model.Recorder import recorder
from model.model import BABCModel, AtnCallback, NERMetrics
import numpy as np
import threading

config = Config()
data_man = DataManger(config)
model = BABCModel(config, len(data_man.label2id), data_man)
model.load_weights(os.path.join(config.root_path, f'checkpoints/${config.save_path}'))
model.compile(optimizer='adam', loss='sparse_categorical_crossentropy',
              metrics=[NERMetrics(name='f1')])
AL = ActiveLearning(model, 50, 'tangs', 'MNLP')
path = './MNLP'
# 找到当前loop
loop = db.find_max_loop(AL.data_pool.data_name)
AL.loop = loop + 1


# 1.计算mnlp分数
def get_select():
    AL.select_samples()
    db.update_status(AL.data_pool.data_name, AL.data_pool.selected_idx, 2)
    db.update_loop(AL.data_pool.data_name, AL.data_pool.selected_idx, AL.loop)


def train_model():
    data_man.config.train_file_name = './MNLP/train.txt'
    x, y = data_man.get_train_data(return_verify=False, slice=False)
    print(x.shape)
    cbk = AtnCallback(score_name='f1',
                      save_model=True,
                      is_record=False,
                      save_dir=AL.model.config.save_path)
    AL.model.fit(x,
                 y,
                 batch_size=10,
                 epochs=20,
                 shuffle=False,
                 validation_data=(AL.x_ver, AL.y_ver),
                 callbacks=cbk
                 )
    his = AL.model.evaluate(AL.x_dev, AL.y_dev)
    with open('./MNLP/f1.txt', 'a+', encoding='utf8') as fp:
        fp.write(str(his[1]) + '\n')

db.reset1()
# get_select()
# train_model()