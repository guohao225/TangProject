# -*- coding = utf-8 -*-
# @Time:
# @Author: GH
import os
import numpy as np
import json
from tensorflow.keras.preprocessing import sequence as seqt
import tensorflow as tf
import pandas as pd
from tqdm import tqdm
import pandas
from tensorflow.keras.preprocessing.text import Tokenizer as TK
from tensorflow.keras.preprocessing import text
from bert4keras.tokenizers import Tokenizer
from itertools import chain
from untils.Config import CONFIG


class DataManger:
    def __init__(self):
        self.config = CONFIG
        self.pre_embedding = []
        # 使用bert做词嵌入还是选择word2vec做词嵌入
        if self.config.use_bert_embedding:
            self.tokenizer = Tokenizer("./checkpoints/pretrain_word/vocab.txt")
            self.vocab_len = self.tokenizer._vocab_size
        else:
            self.tokenizer = Tokenizer('./checkpoints/pretrain_word/vocab.txt',
                                       do_lower_case=True,
                                       token_end=CONFIG.use_bert,
                                       token_start=CONFIG.use_bert)
            self.vocab_len = self.tokenizer._vocab_size
        self.word_tokenizer = TK(filters=None)
        self.label2id, self.id2label = self.label_to_id()
        self.ver_x = []
        self.ver_y = []
        self.ver_mask = []
        self.seg_data = {}
        self.load_segment()
        # tjson = open('./data/seg_tokenizer.json', 'r', encoding='utf8')
        self.seg_tokenizer = Tokenizer(token_dict='./data/segVocab.txt', token_end=None, token_start=None)
        self.seg_vocab_len = self.seg_tokenizer._vocab_size
        # self.seg_tokenizer.word_index

    def bert_embedding_from_file(self, file_name, return_ver=False):
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
        sequence_len = []
        segs = []
        begin = 0
        for index in tqdm(sentence_sep_index):
            sentence_list = train_data.iloc[begin: index, 0].tolist()  # index+1
            sequence_len.append(len(sentence_list))
            seg = self.word_segment(sentence_list)
            segs.append(seg)
            sentence_label = train_data.iloc[begin: index, -1].tolist()
            input_ids, seg_ids = self.tokenizer.encode(sentence_list, maxlen=self.config.max_sequence_len)
            input_ids += [0] * (self.config.max_sequence_len - len(input_ids))
            seg_ids += [0] * (self.config.max_sequence_len - len(seg_ids))
            sentence_label = [self.label2id[label] for label in sentence_label]
            # if self.config.use_bert:
            #     sentence_label.insert(0, 1)
            sentence_label = seqt.pad_sequences([sentence_label], maxlen=self.config.max_sequence_len, padding='post',
                                                truncating='post')
            sentence_label = np.array(sentence_label).reshape(-1).tolist()
            x.append(input_ids)
            y.append(sentence_label)
            att_mask.append(seg_ids)
            begin = index + 1
        x = np.array(x)
        y = np.array(y)
        att_mask = np.array(att_mask)
        sequence_len = np.array(sequence_len)
        segs = np.array(segs)
        samples = len(x)
        index = np.arange(samples)
        np.random.shuffle(index)
        # 打乱样本
        x = x[index]
        y = y[index]
        att_mask = att_mask[index]
        sequence_len = sequence_len[index]
        sequence_len = np.expand_dims(sequence_len, axis=-1)
        sequence_len = np.pad(sequence_len, [(0, 0), (0, CONFIG.max_sequence_len - 1)], mode='constant')
        segs = segs[index]
        if return_ver:
            return x[0: int(CONFIG.ver_rate*samples)], x[int(CONFIG.ver_rate*samples):-1], \
                y[0: int(CONFIG.ver_rate*samples)], y[int(CONFIG.ver_rate*samples):-1],  \
                att_mask[0: int(CONFIG.ver_rate*samples)], att_mask[int(CONFIG.ver_rate*samples):-1],\
                sequence_len[0: int(CONFIG.ver_rate*samples)], sequence_len[int(CONFIG.ver_rate*samples):-1],\
                segs[0: int(CONFIG.ver_rate*samples)], segs[int(CONFIG.ver_rate*samples):-1]
        return x, y, att_mask, sequence_len, segs

    def bert_embedding_sequence(self, sequence, labels, shuffle=True):
        x = []
        y = []
        att_mask = []
        sequence_len = []
        segs = []
        for sen, label in zip(sequence, labels):
            sequence_len.append(len(sen))
            seg = self.word_segment(sen)
            input_ids, seg_ids = self.tokenizer.encode(sen, maxlen=self.config.max_sequence_len)
            input_ids += [0] * (self.config.max_sequence_len - len(input_ids))
            seg_ids += [0] * (self.config.max_sequence_len - len(seg_ids))
            sentence_label = [self.label2id[label] for label in label]
            if self.config.use_bert:
                sentence_label.insert(0, 1)
            sentence_label = seqt.pad_sequences([sentence_label],
                                                maxlen=self.config.max_sequence_len,
                                                padding='post', truncating='post')
            sentence_label = np.array(sentence_label).reshape(-1).tolist()
            x.append(input_ids)
            y.append(sentence_label)
            att_mask.append(seg_ids)
            segs.append(seg)
        x = np.array(x)
        y = np.array(y)
        att_mask = np.array(att_mask)
        sequence_len = np.array(sequence_len)
        segs = np.array(segs)
        if shuffle:
            samples = len(x)
            index = np.arange(samples)
            np.random.shuffle(index)
            # 打乱样本
            x = x[index]
            y = y[index]
            att_mask = att_mask[index]
            sequence_len = sequence_len[index]
            segs = segs[index]
        return x, y, att_mask, sequence_len, segs

    def bert_embedding_sentences(self, sentences):
        tokens = []
        att_mask = []
        sequence_len = []
        segs = []
        for sentence in tqdm(sentences):
            sentence = list(sentence)
            seg = self.word_segment(sentence)
            input_ids, seg_ids = self.tokenizer.encode(sentence, maxlen=self.config.max_sequence_len)
            input_ids += [0] * (self.config.max_sequence_len - len(input_ids))
            seg_ids += [0] * (self.config.max_sequence_len - len(seg_ids))
            tokens.append(input_ids)
            att_mask.append(seg_ids)
            sequence_len.append(len(sentence))
            segs.append(seg)

        return np.array(tokens), np.array(att_mask), np.array(sequence_len), np.array(segs)

    def vocab_from_train(self, sep="\t"):
        df = pd.read_csv(self.config.train_file_name, sep=sep, header=None, names=["word", "token"])
        text = df['word'].tolist()
        text = "".join([str(item) for item in text])
        # print(text)
        self.tokenizer.fit_on_texts(text)

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

    def load_word(self):
        vocab = pandas.read_csv('./data/MSRA/vocab.txt', names=['word'])

    def word_segment(self, sentence):
        word_seg = []
        if len(sentence) > self.config.max_sequence_len:
            sentence = sentence[:self.config.max_sequence_len]
        for word in sentence:
            try:
                word_seg_list = self.seg_data[word]
            except KeyError:
                word_seg_list = ['unk']
            text, _ = self.seg_tokenizer.encode(word_seg_list, maxlen=5)
            if len(text) > 5:
                text = text[0:5]
            text += [0 for item in range(5-len(text))]
            word_seg.append(text)
            # text += [0 for i in range(5)]
            # word_seg += text
        word_seg += [[0 for item in range(5)] for i in range(self.config.max_sequence_len-len(word_seg))]
        # word_seg += [0 for i in range(self.config.max_sequence_len*5-len(word_seg))]
        return word_seg

    def load_segment(self):
        with open("./data/word_seg.txt", 'r', encoding='utf8') as fp:
            self.seg_data = json.load(fp)

    def expand_dim(self,x, dim=4):
        x = np.expand_dims(x, axis=-1)
        x = np.pad(x, [(0, 0), (0, 0), (0, dim)], mode='constant')
        return x

    # 处理训练数据:
    # 目的--为了使下x,mask,segs的维度形同从而进行拼接
    # 原始维度：(x.shape=(len(seq), max_len), mask.shape=(len(seq), max_len), segs=(len(seq), max_len, seg_dim))
    def concat_inputs(self, x, mask, segs):
        x = self.expand_dim(x)
        mask = self.expand_dim(mask)
        # 拼接后的维度为(len(seq), max_len, seg_dim*3)
        x = np.concatenate((x, mask, segs), axis=-1)
        return x


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


data_manger = DataManger()
