# -*- coding = utf-8 -*-
# @Time:
# @Author: GH
import os
import numpy as np
from transformers import BertTokenizer
import tensorflow as tf
import pandas as pd
from tqdm import tqdm
from tensorflow.keras.preprocessing.text import Tokenizer
from itertools import chain
from transformers import TFBertModel
from gensim.models.keyedvectors import KeyedVectors

class DataManger:
    def __init__(self, configure):
        self.config = configure
        self.pre_embedding = []
        # 使用bert做词嵌入还是选择word2vec做词嵌入
        if self.config.use_bert_embedding:
            self.tokenizer = BertTokenizer.from_pretrained("./checkpoints/bert_tiny")
            self.vocab = self.tokenizer.get_vocab()
            self.vocab_len = len(self.vocab)
        elif configure.use_pre_embedding:
            word_index = np.load('./checkpoints/wordvec/word_index.npy', allow_pickle=True).item()
            self.word_index = word_index
            self.vocab_len = len(word_index)
        else:
            self.tokenizer = Tokenizer(filters=' ', oov_token='<unk>', char_level=True)
            self.get_vocab(self.config.train_file_name)
            self.vocab_len = len(self.tokenizer.word_index)
        self.label2id, self.id2label = self.label_to_id()
        self.ver_x = []
        self.ver_y = []
        self.ver_mask = []

    def get_train_data(self, verify_rate=0.8,
                       slice=True,
                       return_mask=False,
                       from_file=True,
                       sequences=None,
                       labels=None,
                       return_verify=True,
                       return_dev=False,
                       ):
        if from_file:
            if self.config.use_bert_embedding:
                x, y, att_mask = self.bert_embedding_from_file(self.config.train_file_name)
            elif self.config.use_pre_embedding:
                x, y = self.load_pre_train_embedding(self.config.train_file_name)
            else:
                x, y, att_mask = self.word2vec_embedding(self.config.train_file_name)
        else:
            if self.config.use_bert_embedding:
                x, y, att_mask = self.bert_embedding_sequence(sequences, labels)
            else:
                x, y, att_mask = self.word2vec_embedding(self.config.train_file_name)

        samples = len(x)
        index = np.arange(samples)
        np.random.shuffle(index)
        
        # 打乱样本
        x = x[index]
        y = y[index]
        att_mask = att_mask[index]
        if return_verify:
            if self.config.ver_file_exist:
                if self.config.use_bert_embedding:
                    x_verify, y_verify, att_mask_verify = self.bert_embedding_from_file(self.config.ver_file_name)
                elif self.config.use_pre_embedding:
                    x_verify, y_verify = self.load_pre_train_embedding(self.config.train_file_name)
                    att_mask_verify = []
                else:
                    x_verify, y_verify, att_mask_verify = self.word2vec_embedding(self.config.ver_file_name)
            else:
                tx = x[0:int(len(x) * verify_rate)]
                ty = y[0:int(len(y) * verify_rate)]
                tmask = att_mask[0:int(len(att_mask)*verify_rate)]
                x_verify = x[int(len(x) * verify_rate):]
                y_verify = y[int(len(y) * verify_rate):]
                x = tx
                y = ty
                att_mask_verify = att_mask[int(len(att_mask) * verify_rate):]
            if slice:
                train_dataset = tf.data.Dataset.from_tensor_slices((x, y, att_mask))
                verify_dataset = tf.data.Dataset.from_tensor_slices((x_verify, y_verify, att_mask_verify))
                return train_dataset, verify_dataset
            else:
                if return_mask:
                    return x, y, x_verify, y_verify, att_mask, att_mask_verify
                # else:
                #     return x, y, x_verify, y_verify
                if return_dev:
                    dev_x = x[int(len(x)*verify_rate):]
                    dev_y = y[int(len(y)*verify_rate):]
                    x = x[0:int(len(x)*verify_rate)]
                    y = y[0:int(len(y)*verify_rate)]
                    return x, y, x_verify, y_verify, dev_x, dev_y
                return x,y,x_verify,y_verify
        return x, y


    def bert_embedding_from_file(self, file_name):
        train_data = pd.read_csv(file_name,
                                 names=['token', 'label'],
                                 delimiter=self.config.file_sep,
                                 skip_blank_lines=False
                                 )
        train_data.fillna('#', inplace=True)
        sentence_sep_index = train_data[train_data["label"] == "#"].index.tolist()
        x = []  # 特征
        y = []  # 标签
        att_mask = []
        begin = 0
        for index in tqdm(sentence_sep_index):
            sentence_list = train_data.iloc[begin: index, 0].tolist()  # index+1
            sentence_label = train_data.iloc[begin: index, -1].tolist()
            if len(sentence_list) < self.config.max_sequence_len - 2:
                # tokenizer.encode返回tmp_x对应词的id
                # 使用bert的tokenizer来分词，此时sentence_list会加入<cls>和<sep>两个符号
                sentence_list = self.tokenizer.encode(sentence_list)
                if not self.config.use_bert:
                    del sentence_list[0]
                    sentence_list.append(0)
                mask = [1] * len(sentence_list)
                # 将sentence_list填充到最大序列长度
                sentence_list += [0 for _ in range(self.config.max_sequence_len - len(sentence_list))]
                try:
                    sentence_label = [self.label2id[label] for label in sentence_label]
                    if self.config.use_bert:
                        sentence_label.insert(0, self.label2id['O'])
                    sentence_label.append(self.label2id['O'])
                except KeyError:
                    print(sentence_list)
                    print(sentence_label)

                # 将标签序列填充到最大长度
                sentence_label += [0 for index in range(self.config.max_sequence_len - len(sentence_label))]
                mask += [0 for index in range(self.config.max_sequence_len - len(mask))]
                x.append(sentence_list)
                y.append(sentence_label)
                att_mask.append(mask)
            else:
                sentence_list = sentence_list[:self.config.max_sequence_len - 2]
                sentence_list = self.tokenizer.encode(sentence_list)
                if not self.config.use_bert:
                    del sentence_list[0]
                    sentence_list.append(0)
                x.append(sentence_list)

                sentence_label = sentence_label[:self.config.max_sequence_len - 2]
                sentence_label = [self.label2id[label] for label in sentence_label]
                if self.config.use_bert:
                    sentence_label.insert(0, self.label2id['O'])
                else:
                    sentence_label.append(self.label2id['O'])
                sentence_label.append(self.label2id['O'])
                y.append(sentence_label)
                mask = [1] * self.config.max_sequence_len
                att_mask.append(mask)
            begin = index + 1
        return np.array(x), np.array(y), np.array(att_mask)
    def bert_embedding_sequence(self, sequence, labels):
        x = []
        y =[]
        att_mask = []
        for sen, label in zip(sequence, labels):
            if len(sen) < self.config.max_sequence_len - 2:
                token_list = self.tokenizer.encode(sen)
                if not self.config.use_bert:
                    del token_list[0]
                    token_list.append(0)
                mask = [1] * len(token_list)
                # 将sentence_list填充到最大序列长度
                token_list += [0 for _ in range(self.config.max_sequence_len - len(token_list))]
                try:
                    token_label = [self.label2id[label] for label in label]
                    if self.config.use_bert:
                        token_label.insert(0, self.label2id['O'])
                    token_label.append(self.label2id['O'])
                except KeyError:
                    print(token_list)
                    print(token_label)
                    # 将标签序列填充到最大长度
                token_label += [0 for index in range(self.config.max_sequence_len - len(token_label))]
                mask += [0 for index in range(self.config.max_sequence_len - len(mask))]
                x.append(token_list)
                y.append(token_label)
                att_mask.append(mask)
            else:
                sen = sen[:self.config.max_sequence_len - 2]
                token_list = self.tokenizer.encode(sen)
                if not self.config.use_bert:
                    del token_list[0]
                    token_list.append(0)
                x.append(token_list)

                token_label = label[:self.config.max_sequence_len - 2]
                token_label = [self.label2id[label] for label in token_label]
                if self.config.use_bert:
                    token_label.insert(0, self.label2id['O'])
                else:
                    token_label.append(self.label2id['O'])
                token_label.append(self.label2id['O'])
                y.append(token_label)
                mask = [1] * self.config.max_sequence_len
                att_mask.append(mask)
        return np.array(x), np.array(y), np.array(att_mask)
    def bert_embedding_sentences(self, sentences):
        lens = []
        tokens = []
        for sentence in sentences:
            sentence = list(sentence)
            lens.append(len(sentence))
            if len(sentence) <= self.config.max_sequence_len - 2:
                word_embedding = self.tokenizer.encode(sentence)
                word_embedding += [0 for i in range(self.config.max_sequence_len - len(word_embedding))]
            else:
                sentence = sentence[:self.config.max_sequence_len - 2]
                word_embedding = self.tokenizer.encode(sentence)
            if not self.config.use_bert:
                del word_embedding[0]
                del word_embedding[-1]
                word_embedding += [0, 0]
            tokens.append(word_embedding)
        return tf.convert_to_tensor(tokens), lens, sentences
    # 传统词嵌入的数据格式构造
    def word2vec_embedding(self, file_name):
        train_data = pd.read_csv(file_name,
                                 names=['token', 'label'],
                                 delimiter=self.config.file_sep)
        sentence_sep_index = train_data[train_data["label"] == '#'].index.tolist()
        begin = 0
        sentences = []
        labels = []
        masks = []
        for index in tqdm(sentence_sep_index):
            sentence_list = train_data.iloc[begin: index, 0].tolist()  # index+1
            sentence_label = train_data.iloc[begin: index, -1].tolist()
            sentence_list = "".join(sentence_list)
            # if self.config.use_pre_embedding:
            #     sequence = [self.tokenizer.word_index[word] for word in sentence_list]
            # else:
            sequence = self.tokenizer.texts_to_sequences(sentence_list)
            # sequence = list(chain.from_iterable(sequence))
            padded_sequence = tf.keras.preprocessing.sequence.pad_sequences([sequence],
                                                                            maxlen=self.config.max_sequence_len,
                                                                            padding="post", truncating="post")
            sentence_list = np.array(padded_sequence).reshape(-1).tolist()
            sentences.append(sentence_list)

            mask = [1] * len(sentence_list)
            padded_mask = tf.keras.preprocessing.sequence.pad_sequences([mask], maxlen=self.config.max_sequence_len,
                                                                           padding="post", truncating="post")
            mask = np.array(padded_mask).reshape(-1).tolist()
            masks.append(mask)

            label = [self.label2id[label] for label in sentence_label]
            sentence_label = tf.keras.preprocessing.sequence.pad_sequences([label],
                                                                           maxlen=self.config.max_sequence_len,
                                                                           padding="post", truncating="post")
            sentence_label = np.array(sentence_label).reshape(-1).tolist()
            labels.append(sentence_label)
            begin = index+1
        sentences = np.array(sentences)
        labels = np.array(labels)
        masks = np.array(masks)
        return sentences, labels, masks

    def load_pre_train_embedding(self, filename):
        train_data = pd.read_csv(filename,
                                 names=['token', 'label'],
                                 delimiter=" ")
        sentence_sep_index = train_data[train_data["label"] == '#'].index.tolist()
        begin = 0
        sentences = []
        labels = []
        padding = np.zeros(300)
        self.word_index["<PAD>"] = padding
        for index in tqdm(sentence_sep_index):
            sentence_list = train_data.iloc[begin: index, 0].tolist()  # index+1
            sentence_label = train_data.iloc[begin: index, -1].tolist()
            if len(sentence_list) > self.config.max_sequence_len:
                sentence_list = sentence_list[0:self.config.max_sequence_len]
            else:
                sentence_list += ['<PAD>' for i in range(self.config.max_sequence_len - len(sentence_list))]
            sentence_list = [word if word in self.word_index else "<PAD>" for word in sentence_list]
            embedding = [self.word_index[word] for word in sentence_list]
            sentences.append(embedding)
            label = [self.label2id[label] for label in sentence_label]
            sentence_label = tf.keras.preprocessing.sequence.pad_sequences([label],
                                                                           maxlen=self.config.max_sequence_len,
                                                                           padding="post", truncating="post")
            sentence_label = np.array(sentence_label).reshape(-1).tolist()
            labels.append(sentence_label)
            begin = index + 1
        sentences = tf.convert_to_tensor(sentences)
        labels = np.array(labels)
        return sentences, labels


    def word2vec_embedding_sentence(self, sentence):
        sentence = list(sentence)
        sequence = self.tokenizer.texts_to_sequences(sentence)
        sequence = list(chain.from_iterable(sequence))
        padded_sequence = tf.keras.preprocessing.sequence.pad_sequences([sequence], maxlen=self.config.max_sequence_len,
                                                                        padding="post", truncating="post")
        sequence = np.array(padded_sequence).reshape(-1)
        label = [self.label2id['O']] * self.config.max_sequence_len
        sequence = np.reshape(sequence, (1, *sequence.shape))
        return tf.convert_to_tensor(sequence), tf.convert_to_tensor(np.array([label]))

    def vocab_from_train(self, sep="\t"):
        df = pd.read_csv(self.config.train_file_name, sep=sep, header=None, names=["word", "token"])
        text = df['word'].tolist()
        text = "".join([str(item) for item in text])
        # print(text)
        self.tokenizer.fit_on_texts(text)

    def get_vocab(self, file_name):
        # print(self.config.vocab_name)
        train_data = pd.read_csv(file_name,
                                 names=['token', 'label'],
                                 delimiter=self.config.file_sep,
                                 skip_blank_lines=False
                                 )
        sentence_sep_index = train_data[train_data["token"] == "#"].index.tolist()
        begin = 0
        seq = []
        for index in tqdm(sentence_sep_index):
            sentence_list = train_data.iloc[begin: index, 0].tolist()  # index+1
            sentence_list = "".join(sentence_list)
            seq.append(sentence_list)
            begin = index + 1
        self.tokenizer.fit_on_texts(seq)

    def label_to_id(self):
        df_label = pd.read_csv(self.config.label_name, names=['label', 'id'], delimiter=' ')
        label2id = {}
        id2label = {}
        for index, record in df_label.iterrows():
            label = record.label
            label_id = record.id
            label2id[label] = label_id
            id2label[label_id] = label
        return label2id, id2label
    def get_test_data(self, filename, slice=False):
        x, y, mask = self.bert_embedding(filename)
        samples = len(x)
        index = np.arange(samples)
        np.random.shuffle(index)
        # 打乱样本
        x = x[index]
        y = y[index]
        att_mask = mask[index]
        if slice:
            return tf.data.Dataset.from_tensor_slices((x, y, att_mask))
        return x, y, att_mask




def get_real_sequence(data, lens):
    examples = []
    for i in range(len(lens)):
        if len(data.shape) == 2:
            example = data[i, :lens[i]]
        else:
            example = data[i, len[i], :]
        print(example.shape)
        examples.append(example)
    # 转换为 NumPy 数组
    examples = np.array(examples)
    return examples

