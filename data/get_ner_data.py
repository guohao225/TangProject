import random
import sqlite3
import pandas
import json
import numpy as np

conn = sqlite3.connect('./source.db')
cur = conn.cursor()

def fix():
    data = cur.execute("select id, content, entitys from alltangs where loop > 0")
    data = data.fetchall()

    for item in data:
        pid = item[0]
        content = json.loads(item[1])
        content = "".join(content)
        content = list(content)
        label = ["O" for i in range(len(content))]
        entitys = json.loads(item[2])
        for en in entitys:
            if len(en) != 5:
                continue
            tp = en[0]
            label[en[2]] = 'B-' + tp
            for i in range(en[2]+1, en[3]+1):
                try:
                    label[i] = 'I-' + tp
                except IndexError:
                    continue
        cur.execute('update alltangs set user_label = ? where id = ?', (json.dumps(label), pid))
        print(f"更新{pid}")

    conn.commit()

def gen():
    data = cur.execute("select content, user_label from alltangs where loop>0")
    data = data.fetchall()
    words = []
    tokens = []
    for item in data:
        content = json.loads(item[0])
        label = json.loads(item[1])
        content = "".join(content)
        content = list(content)
        if len(content) > len(label):
            content = content[:len(label)]
        else:
            label = label[:len(content)]
        content.append("#")
        label.append("#")
        words += content
        tokens += label
    pd = pandas.DataFrame({'words': words, 'tokens': tokens})
    pd.to_csv('NerTrain.txt', index=None, header=None, sep=' ')

# 数据增强
def data_strong():
    miss  = 0
    data = cur.execute("select content, user_label from alltangs where loop>130")
    data = data.fetchall()
    strong_data = []
    for item in data:
        content = json.loads(item[0])
        label = json.loads(item[1])
        begin = 0
        label_list = []
        if len(content) <= 2:
            continue
        # print(content)
        # print(label)
        for sen in content:
            sen_list = label[begin:begin + len(sen)]
            begin = begin + len(sen)
            label_list.append(sen_list)
        shuffle_index = [i for i in range(len(content))]
        random.shuffle(shuffle_index)
        strong_data.append(([content[index] for index in shuffle_index],
                            [label_list[index] for index in shuffle_index]))
    return strong_data

def strong_data_process():
    data = data_strong()
    words = []
    tokens = []
    for content, label in data:
        content = "".join(content)
        label = [element for sublist in label for element in sublist]
        content = list(content)
        if len(content) != len(label):
            print(content)
            print(label)
        content.append("#")
        label.append("#")
        words += content
        tokens += label
    pd = pandas.DataFrame({'words': words, 'tokens': tokens})
    pd.to_csv('Strong.txt', index=None, header=None, sep=' ')

# fix()
# gen()
strong_data_process()


