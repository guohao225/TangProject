# -*- coding = utf-8 -*-
# @Time:
# @Author: GH
import csv
import json
import os
import random
import sys
from easydict import EasyDict
from untils.PathManger import get_root_path
import numpy as np
import pandas as pd

# 定义提取配置属性与属性值对应的字典
Map = {
    'DATA': 'data',
    'MODEL_CONFIG': 'model_config',
    'LABEL_CONFIG': 'label_config',
    'TRAIN_CONFIG': 'train_config',
    "describe": "describe"
}
configMap = EasyDict(Map)


def reset_config_file():
    root = get_root_path()
    backup_model_config = os.path.join(root, 'model/model_backup.json')
    model_config = os.path.join(root, 'model/model.json')
    with open(backup_model_config, "r", encoding='utf8') as fp:
        backup_data = json.load(fp)
        fp.close()
    with open(model_config, "w+", encoding='utf8') as fp:
        json.dump(backup_data, fp, ensure_ascii=False, indent=4)
        fp.close()


class Config:
    def __init__(self, config_file="../model/model.json"):
        root = get_root_path()
        config_file = os.path.join(root, "model/model.json")
        with open(config_file, encoding='utf-8') as fp:
            config_dic = json.load(fp)
        data_config = config_dic[configMap.DATA]
        model_config = config_dic[configMap.MODEL_CONFIG]
        label_config = config_dic[configMap.LABEL_CONFIG]
        train_config = config_dic[configMap.TRAIN_CONFIG]

        self.set_attr(data_config)
        self.set_attr(model_config)
        self.set_attr(label_config)
        self.set_attr(train_config)

        self.ver_file_exist = False
        self.is_file_exist()
        self.root_path = get_root_path()

    # 将配置项存为成员变量
    def set_attr(self, dic):
        for key in dic:
            if key != configMap.describe:
                self.__setattr__(key, dic[key])
            else:
                break

    def is_file_exist(self):
        root_path = get_root_path()
        data_dir = os.path.join(root_path, self.data_dir)
        if not os.path.exists(data_dir):
            raise Exception("数据文件夹不存在，请检查配置是否正确")
        self.data_dir = data_dir

        train_file_path = os.path.join(data_dir, self.train_file_name)
        if not os.path.exists(train_file_path):
            raise Exception("训练文件不存在，请检查配置是否正确")
        self.train_file_name = train_file_path

        ver_file_path = os.path.join(data_dir, self.ver_file_name)
        if os.path.exists(ver_file_path):
            self.ver_file_exist = True
            self.ver_file_name = ver_file_path

        vocab_dir = os.path.join(root_path, self.vocab_dir)
        if not os.path.exists(vocab_dir):
            raise Exception("词表文件夹不存在，请检查配置是否正确")
        self.vocab_dir = vocab_dir

        vocab_path = os.path.join(vocab_dir, self.vocab_name)
        if not os.path.exists(vocab_path):
            raise Exception("词表文件不存在，请检查配置是否正确")
        self.vocab_name = vocab_path

        label_path = os.path.join(vocab_dir, self.label_name)
        self.label_name = label_path
        if not os.path.exists(label_path):
            self.create_label2id()

        checkpoints_dir = os.path.join(root_path, self.checkpoints_dir)
        if not os.path.exists(checkpoints_dir):
            os.mkdir(checkpoints_dir)

    # 设置随机数种子
    def set_seed(self, seed=None):
        # random.seed()俗称为随机数种子
        # 不设置随机数种子，你每次随机抽样得到的数据都是不一样的。设置了随机数种子，能够确保每次抽样的结果一样。
        if seed is None:
            random.seed(self.seed)
            np.random.seed(self.seed)
            os.environ["PYTHONHASHSEED"] = str(self.seed)
        else:
            random.seed(seed)
            np.random.seed(seed)
            os.environ["PYTHONHASHSEED"] = str(self.seed)

    def create_label2id(self):
        entity_label = []
        label_id = []
        i = 1
        for entity_prefix in self.label_prefix[:-1]:
            for entity_suffix in self.label_suffix:
                label_name = entity_prefix + "-" + entity_suffix
                entity_label.append(label_name)
                label_id.append(i)
                i += 1
        entity_label.append('O')
        label_id.append(i)
        entity_label.append('[PAD]')
        label_id.append(0)
        dic = {
            'label': entity_label,
            'id': label_id
        }
        label2id = pd.DataFrame(dic)
        label2id.to_csv(self.label_name, header=None, index=None, quoting=csv.QUOTE_NONE, sep=' ')

    def get_train_config(self, use_to_web=False):
        config = {
            "multi_head_num": self.multi_head_num,
            'embedding_dim': self.embedding_dim,
            'hidden_dim': self.hidden_dim,
            'attention_dim': self.attention_dim,
            'max_sequence_len': self.max_sequence_len,
            'epochs': self.epochs,
            'batch_size': self.batch_size,
            'droupout': self.droupout,
            'regularizers_coeffiicient': self.regularizers_coeffiicient,
            'learning_rate': self.learning_rate,
            'atn_regularizers_coeffiicient': self.atn_regularizers_coeffiicient
        }
        if use_to_web:
            config['bert_model_name'] = self.bert_model_name
            config['attention_type'] = self.attention_type
        return config

    def get_baseline_config(self):
        config = {
            "ver_model": self.ver_model,
            "embedding_dim":self.embedding_dim,
            "use_bert": int(self.use_bert),
            "max_sequence_len":self.max_sequence_len,
            "droupout": self.droupout,
            "learning_rate": self.learning_rate,
            "regularizers_coeffiicient":self.regularizers_coeffiicient
        }
        return config

    def generate_baseline_name(self, sep="_"):
        config = self.get_baseline_config()
        name_list = [config[key] for key in config]
        name = sep.join(str(x) for x in name_list)
        return name

    def set_config(self, dic, save_to_file=False):
        for key in dic:
            self.__setattr__(key, dic[key])
        if save_to_file:
            root = get_root_path()
            model_config = os.path.join(root, 'model/model.json')
            with open(model_config, "r", encoding='utf8') as fp:
                json_data = json.load(fp)
                fp.close()
            for key in dic:
                if key == 'bert__name':
                    json_data['model_config']['bert_model_name'] = dic[key]
                if key == 'attention_type':
                    json_data['model_config']['attention_type'] = int(dic[key])
                if key == 'embedding_dim':
                    json_data['model_config']['embedding_dim'] = int(dic[key])
                if key == 'hidden_dim':
                    json_data['model_config']['hidden_dim'] = int(dic[key])
                if key == 'max_sequence_len':
                    json_data['model_config']['max_sequence_len'] = int(dic[key])
                if key == 'epochs':
                    json_data['train_config']['epochs'] = int(dic[key])
                if key == 'batch_size':
                    json_data['train_config']['batch_size'] = int(dic[key])
                if key == 'learning_rate':
                    json_data['train_config']['learning_rate'] = float(dic[key])
                if key == 'droupout':
                    json_data['train_config']['droupout'] = float(dic[key])
                if key == 'regularizers_coeffiicient':
                    json_data['train_config']['regularizers_coeffiicient'] = float(dic[key])
            with open(model_config, "w+", encoding='utf8') as fp:
                json.dump(json_data, fp, ensure_ascii=False, indent=4)

    def generate_checkpoints_name(self):
        train_cofig = self.get_train_config()
        file_name_list = [train_cofig[key] for key in train_cofig]
        file_name_list.insert(0, self.attention_type)
        file_name = "_".join(str(x) for x in file_name_list)
        checkpoint_dir = os.path.join(self.root_path, f'{self.checkpoints_dir}/{file_name}')
        return file_name, checkpoint_dir


CONFIG = Config()