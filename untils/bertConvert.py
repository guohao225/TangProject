# @time:2023/2/28 17:36
# @functional:
import tensorflow as tf
import torch
import os
import numpy as np

from transformers import BertModel, AutoModelForCausalLM, BertTokenizer, TFBertModel
#
# # 加载预训练的Bert模型
pt_model = TFBertModel.from_pretrained("../checkpoints/MiniRBT-h256-pt", from_pt=True)
# #
# # # 将模型保存为TensorFlow 2格式
tf_model_path = "../checkpoints/MiniRBT-h256-pt/bert_model"
tf_model = pt_model.save_pretrained(tf_model_path)

# 加载TensorFlow 2格式的模型
#
# c = tf.constant([[1, 2], [3, 4], [5, 6]])
# m = tf.constant([[1, 2], [3, 4], [5, 6]])
# s = loaded_model(c)
# print(s)
# # print(s)
# # from itertools import chain
# # data = [["ijhdfa"],['sdcdf'], ['dedasf']]
# # # ls = list("".join(data))
# # print(list("".join(chain.from_iterable(data))))

# bert_mode = TFBertModel.from_pretrained("../checkpoints/MiniRBT-h256-pt")
# print(bert_mode)
# import bert4keras.models as b4k
# model = b4k.build_transformer_model('../checkpoints/MiniRBT-h256-pt/albert_config_tiny_g.json',
#                             "../checkpoints/MiniRBT-h256-pt/albert_model.ckpt",
#                             model='albert', return_keras_model=True)
# model.summary()


## 处理预训练词向量
