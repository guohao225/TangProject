import json
import os
from itertools import chain
from keras_self_attention import SeqSelfAttention
from untils import Config as config
from untils import DataManger
from model import model
from untils.PathManger import get_root_path
import tensorflow as tf
from untils import evaluate as eva

# os.environ["CUDA_VISIBLE_DEVICES"] = "-1"
gpu_devices = tf.config.experimental.list_physical_devices('GPU')
for device in gpu_devices: tf.config.experimental.set_memory_growth(device, True)

y_lose = []
x_lose = ""
y_acc = []
val_f1 = []

TRAIN_STATUS = True
BEGAIN_VAL = False

root = get_root_path()
configure = config.Config(os.path.join(root, "model/model.json"))
configure.set_seed()
tf.random.set_seed(42)
data_manger = DataManger.DataManger(configure)
# train_dataset, val_dataset = data_manger.get_train_data()
train_dataset = []
val_dataset = []
EPOCH_LOG = []
X = []

def create_ckpt(use_exist_model=False):
    bbc_model = model.BABCModel(configure, len(data_manger.label2id), data_manger)
    optimizer = tf.keras.optimizers.Adam(learning_rate=configure.learning_rate)
    CHECKPOINT_DIR = configure.generate_checkpoints_name()[1]
    CHECKPOINT_NAME = "ATNBILSTM"
    checkpoint = tf.train.Checkpoint(bbc_model=bbc_model, optimizer=optimizer)
    ckpt_manger = tf.train.CheckpointManager(checkpoint,
                                             directory=CHECKPOINT_DIR,
                                             checkpoint_name=CHECKPOINT_NAME,
                                             max_to_keep=1)
    if use_exist_model:
        checkpoint.restore(ckpt_manger.latest_checkpoint)
    return bbc_model, optimizer, ckpt_manger


def save_model(ckpt_manger):
    ckpt_manger.save()


def create_model(model_path=None):
    new_model = model.BABCModel(configure, len(data_manger.id2label), data_manger)
    if model_path is not None:
        new_model.load_weights(model_path)
    return new_model


# atn_model = model.BABCModel(configure, len(data_manger.id2label), data_manger)
# name, dir = configure.generate_checkpoints_name()
# atn_model.load_weights(dir)
def predict(sentence, atn_model):
    sen_len = len(sentence)
    # model, opt, ckpt = create_ckpt(use_exist_model=True)
    sequence, _, _1, _2 = data_manger.bert_embedding_sentence(sentence)
    # label, score = model(sequence, return_decode_score=True)
    label, score = atn_model(sequence, return_decode_score = True)
    label = label[:, 0:sen_len]
    score = score[:, 0:sen_len]
    label = tf.reshape(label, [-1]).numpy()
    score = tf.reshape(score, [-1]).numpy()
    data = []
    for i in range(sen_len):
        data.append({"word": sentence[i], "label": int(label[i]), "score": float(score[i])})
    return data


def predict_poem(item, sentences, ner_model):
    sen_len = [len(sen) for sen in sentences]
    input_sentence = "".join(sentences)
    sequence, _, _1, _2 = data_manger.bert_embedding_sentence(input_sentence)
    label, _, _1, _2 = ner_model(sequence)
    label = eva.token_to_label(label.numpy(), data_manger.id2label)
    label = list(chain.from_iterable(label))
    if len(label) < len(input_sentence):
        label += ['O' for i in range(len(input_sentence)-len(label))]
    start = 0
    end = sen_len[0]
    labels = []
    labels_pos = []
    entitys = []
    for i in range(len(sen_len)):
        token = label[start:end]
        start = end
        if i == (len(sen_len) - 1):
            end = -1
        else:
            end += sen_len[i+1]
        if len(token) != sen_len[i]:
            print("转换失败")
            return
        labels.append(token)
        label_pos = []
        eva.entity_pos_extraction("".join(token), 0, label_pos)
        entity = [sentences[i][start:end] for start, end in label_pos]
        entitys += entity
        label_pos = [[i, t[0], t[1]] for t in label_pos]
        labels_pos += label_pos
    item['labels'] = labels
    item["labels_pos"] = labels_pos
    item['entitys'] = entitys



# x, y, x_ver, y_ver = data_manger.get_train_data(slice=False)
# nermodel = model.BaseLineModel(data_manger.vocab_len, 200, 32, 24)
# nermodel.compile(optimizer=Adam(learning_rate=0.001), loss=nermodel.decoder.loss,
#                  metrics=[model.NERMetrics(name='f1')])
# history = nermodel.fit(x, y, batch_size=100, epochs=20, validation_data=(x_ver, y_ver))
#
# import matplotlib.pyplot as plt
# x = history.history['f1']
# y = history.history['val_f1']
# plt.plot(x)
# plt.plot(y)
# plt.title('loss')
# plt.ylabel('loss')
# plt.xlabel('epoch')
# i = 0
# for a, b in (zip(x, y)):
#     if i%5 == 0:
#         plt.text(a, b, b, ha='center', va='bottom', fontsize=10)
#     i += 1
# plt.show()