import json
import operator
import re
from functools import reduce

import pandas

import untils.DataBase as db

# 从数据库中抽取出古诗训练集
def extract_train():
    coll = db.open_collection('POEMDATA', 'poem')
    data = coll.find()
    words = []
    words_labels = []
    for item in data[0: 1802]:
        content = item['paragraphs']
        for i in range(len(content)):
            if len(item['labels'][i]) < len(content[i]):
                item['labels'][i] += ['O' for _ in range(len(content[i])-len(item['labels'][i]))]
                print(f"{len(item['labels'][i])}:{len(content[i])}")
            elif len(item['labels'][i]) > len(content[i]):
                item['labels'][i] = item['labels'][i][0:len(content[i])]
        content = list("".join(content))
        content.append("#")
        labels = reduce(operator.add, item['labels'])
        labels.append('O')
        if len(content) != len(labels):
            print(f"出错了---id是：{item['_id']}:长度为：{len(content)}:{len(labels)}")
        words += content
        words_labels += labels
    pd = pandas.DataFrame({'words': words,
                           'labels': words_labels})
    pd.to_csv("../source/poemTrain.csv", encoding='utf8', header=None, index=None, sep=' ')

# 去掉人民日报中的空格
def datapro():
    pd = pandas.read_csv("../data/RenMinRiBao/test.txt", header=None, delimiter=' ')
    pd = pd.dropna()
    pd.to_csv('../source/train.csv', header=None, index=None, sep=' ', encoding='utf8')


def re_id_poem():
    coll = db.open_collection('POEMDATA', 'poem')
    coll.delete_many({})
    with open("../source/POEMDATA-poem.json", 'r', encoding="utf-8") as fp:
        data = json.load(fp)
    i = 0
    for item in data:
        item["_id"] = i
        coll.insert_one(item)
        i += 1

# 拆分先秦语料
def splitDataset():
    labels = open('../source/target.txt', 'r', encoding='utf8')
    CH = open('../source/source.txt','r', encoding='utf8')
    CH = CH.readlines()
    i = 0
    labels = labels.readlines()
    print(len(CH))
    print(len(labels))
    res_word = []
    res_label = []
    for word, label in zip(CH, labels):
        label = re.sub(r'B-JOB|I-JOB|B-BOO|I-BOO|B-WAR|I-WAR|B-ORG|I-ORG', 'O', label)
        label = label.replace('\n', "")
        word = word.replace('\n', "")
        label = label.split(" ")
        word = word.split(" ")
        label.append("O")
        word.append("#")
        res_word.extend(word)
        res_label.extend(label)
        # if len(word) == len(label):
        #     print(word)
        #     print(label)
        #     print(i)
        #     i += 1
    pd = pandas.DataFrame({'word':res_word, 'label':res_label})
    pd.to_csv('../source/train.csv', header=None, index=None, sep=' ')
    # print(pd)


extract_train()