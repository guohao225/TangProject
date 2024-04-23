# @time:2023/9/3 16:29
# @functional:
import os
import re
import json
import sys
import numpy as np
from bert4keras.tokenizers import Tokenizer
from model_config import CONFIG
from tensorflow.keras.preprocessing import text as token
from tqdm import tqdm

np.random.seed(42)

class PrarmterManger():
    def __init__(self, data_path='./datasets/liter'):
        self.data_path = data_path
        self.parser = {}
        self.parser_init()

    def parser_init(self):
        self.parser["train_file"] = f'{self.data_path}/train.txt'
        self.parser["val_file"] = f'{self.data_path}/valid.txt'
        self.parser['test_file'] = f'{self.data_path}/test.txt'
        self.parser["tags_file"] = f'{self.data_path}/relation2id.txt'


class DataLoader():
    def __init__(self, max_len=128, segment=False):
        self.paramter_man = PrarmterManger()
        if CONFIG.use_bert:
            self.tokenizer = Tokenizer('./tiny_bert/guwen_bert/vocab.txt')
        else:
            self.tokenizer = Tokenizer('./tiny_bert/vocab.txt', token_end=None, token_start=None)
        self.max_len = max_len
        self.tag2id, self.id2tag = self.load_tags()
        self.segment = segment
        if segment:
            self.seg_data = self.load_segment()
            tjson = open('./datasets/seg_tokenizer.json', 'r', encoding='utf8')
            self.seg_tokenizer = token.tokenizer_from_json(json.load(tjson))

    def load_tags(self):
        with open(self.paramter_man.parser['tags_file'], 'r', encoding='utf8') as f:
            tagset = re.split(r'\s+', f.read().strip())
        return dict((tag, idx) for idx, tag in enumerate(tagset)), dict((idx, tag) for idx, tag in enumerate(tagset))


    def load_segment(self):
        seg_data = {}
        with open("./datasets/word_seg.txt", 'r', encoding='utf8') as fp:
            seg_data = json.load(fp)
        return seg_data

    def convert_pos_to_mask(self, pos):
        e_pos_mask = [0] * self.max_len
        for i in range(pos[0], pos[1]):
            e_pos_mask[i] = 1
        return e_pos_mask

    def load_train_data2(self, file_type):
        tokens = []
        labels = []
        en_pos = []
        relative_pos1 = []
        relative_pos2 = []
        segment = []
        segment_ids = []

        all_entity1_tokens = []
        all_entity2_tokens = []
        all_entity1_ids = []
        all_entity2_ids = []

        with open(self.paramter_man.parser[file_type], 'r', encoding='utf-8') as f_in:
            for line in tqdm(f_in):
                try:
                    line = line.strip()
                    item = json.loads(line)
                    sentence = item['text']
                    pos1 = item['h']['pos']
                    pos2 = item['t']['pos']
                    label = self.tag2id[item['relation']]
                    indexed_tokens, seg_ids = self.encode_and_padding(sentence)

                    entity1_tokens, entity1_ids = self.encode_and_padding(sentence[pos1[0]:pos1[1]])
                    entity2_tokens, entity2_ids = self.encode_and_padding(sentence[pos2[0]:pos2[1]])
                    all_entity1_tokens.append(entity1_tokens)
                    all_entity2_tokens.append(entity2_tokens)
                    all_entity1_ids.append(entity1_ids)
                    all_entity2_ids.append(entity2_ids)

                    if self.segment:
                        word_seg = self.word_segment(sentence)
                        segment.append(word_seg)

                    pos_mask, re_pos1, re_pos2 = self.pos_encode(sentence, pos1, pos2)
                    tokens.append(indexed_tokens)
                    segment_ids.append(seg_ids)
                    relative_pos1.append(re_pos1)
                    relative_pos2.append(re_pos2)
                    en_pos.append(pos_mask)
                    labels.append(label)
                except:
                    continue
        tokens = np.array(tokens)
        segment_ids = np.array(segment_ids)
        labels = np.array(labels)
        en_pos = np.array(en_pos)
        relative_pos1 = np.array(relative_pos1)
        relative_pos2 = np.array(relative_pos2)
        all_entity1_tokens = np.array(all_entity1_tokens)
        all_entity2_tokens = np.array(all_entity2_tokens)
        all_entity1_ids = np.array(all_entity1_ids)
        all_entity2_ids = np.array(all_entity2_ids)


        samples = len(labels)
        index = np.arange(samples)
        np.random.shuffle(index)
        tokens = tokens[index]
        segment_ids = segment_ids[index]
        labels = labels[index]
        en_pos = en_pos[index]
        relative_pos1 = relative_pos1[index]
        relative_pos2 = relative_pos2[index]
        all_entity1_tokens = all_entity1_tokens[index]
        all_entity2_tokens = all_entity2_tokens[index]
        all_entity1_ids = all_entity1_ids[index]
        all_entity2_ids = all_entity2_ids[index]
        if self.segment:
            segment = np.array(segment)
            segment = segment[index]
            return tokens, segment_ids, en_pos, labels, relative_pos1, relative_pos2, segment
        return \
            tokens, segment_ids, en_pos, labels, relative_pos1, relative_pos2, \
            (all_entity1_tokens, all_entity1_ids), (all_entity2_tokens, all_entity2_ids)

    def pos_encode(self, sentence, range1, range2):
        if len(sentence) > self.max_len:
            sentence = sentence[0:self.max_len-1]
        # pos1_mask = self.max_len + 1
        # pos2_mask = self.max_len + 2
        pos1_mask = 0
        pos2_mask = 0
        cur_index = 1
        encode_list = []
        range1_relative_pos = []
        range2_relative_pos = []
        range1_pos = 0
        for index in range(len(sentence)):
            if index in range(range1[0], range1[1]):
                encode_list.append(pos1_mask)
            elif index in range(range2[0], range2[1]):
                encode_list.append(pos2_mask)
            else:
                encode_list.append(cur_index)
                cur_index += 1
        for index in range(self.max_len):
            if index < range1[0]:
                range1_relative_pos.append(index-range1[0])
            elif index > range1[1]-1:
                range1_relative_pos.append(index-range1[1])
            else:
                range1_relative_pos.append(0)
        for index in range(self.max_len):
            if index < range2[0]:
                range2_relative_pos.append(index-range2[0])
            elif index > range2[1]-1:
                range2_relative_pos.append(index-range2[1])
            else:
                range2_relative_pos.append(0)
        encode_list += [0 for i in range(self.max_len-len(encode_list))]
        range1_relative_pos += [0 for i in range(self.max_len-len(range1_relative_pos))]
        range2_relative_pos += [0 for i in range(self.max_len-len(range2_relative_pos))]
        return encode_list, range1_relative_pos, range2_relative_pos

    def word_segment(self, sentence):
        if not self.segment:
            return []
        word_seg = []
        if len(sentence) > self.max_len:
            sentence = sentence[:self.max_len]
        for word in sentence:
            try:
                word_seg_list = self.seg_data[word]
            except KeyError:
                word_seg_list = ['unk']
            text = [self.seg_tokenizer.word_index[word] for word in word_seg_list]
            if len(text) > 5:
                text = text[0:5]
            text += [0 for item in range(5-len(text))]
            word_seg.append(text)
        word_seg += [[0 for item in range(5)] for i in range(self.max_len-len(word_seg))]
        return word_seg

    def encode_and_padding(self, sentence):
        indexed_tokens, seg_ids = self.tokenizer.encode(sentence, maxlen=self.max_len)
        indexed_tokens += [0] * (self.max_len - len(indexed_tokens))
        seg_ids += [0] * (self.max_len - len(seg_ids))
        return indexed_tokens, seg_ids
    def get_vocab_size(self):
        return self.tokenizer._vocab_size