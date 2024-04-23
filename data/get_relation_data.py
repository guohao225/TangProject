import sqlite3
import json
import random

conn = sqlite3.connect('./source.db')
cur = conn.cursor()

def get_data():
    data = cur.execute('select relations from alltangs where relations is not null and ((loop >=0 and loop <=30) or (loop >=119 and loop<=150))')
    data = [item[0] for item in data.fetchall()]
    relations = []
    for item in data:
        item = eval(item)
        relations += item

    relation_types = [item['relation'] for item in relations]
    relation_types = set(relation_types)

    train = open('RE_TRAIN/train1.txt', 'w', encoding='utf-8')
    label = open('RE_TRAIN/label1.txt', 'w', encoding='utf-8')
    for item in relations:
        train.write(json.dumps(item, ensure_ascii=False) + '\n')
    for item in relation_types:
        label.write(item + '\n')
    train.close()
    label.close()

def strong_data():
    with open('RE_TRAIN/train1.txt', 'r', encoding='utf-8') as f:
        lines = f.readlines()
    data = []
    unkonw_data = []
    for line in lines:
        jn_data = json.loads(line)
        re = jn_data['relation']
        if re not in ['某时某地', '位于', '对仗', '包含', '未知']:
            data.append(jn_data)
        if re == '未知':
            unkonw_data.append(jn_data)

    shuffle_index = [i for i in range(len(data))]
    random.shuffle(shuffle_index)
    shuffle_index = shuffle_index[0:1700]
    shuffle_data = [data[i] for i in shuffle_index]
    for e in shuffle_data:
        h = e['h']['pos']
        h_name = e['h']['name']
        t = e['t']['pos']
        t_name = e['t']['name']
        text = e['text']
        relation = e['relation']
        try:
            text = text[h[0]:t[1]]
        except:
            continue
        new_h = [0, len(h_name)]
        new_t = [len(text)-len(t_name),  len(text)]
        item = {'text':text, 'h':{'name':h_name, 'pos':new_h}, 't':{'name':t_name, 'pos':new_t}, 'relation':relation}
        data.append(item)
    data = data + unkonw_data[0: 9000-len(data)]
    train = open('RE_TRAIN/train1.txt', 'w', encoding='utf-8')
    for item in data:
        train.write(json.dumps(item, ensure_ascii=False) + '\n')
    train.close()

def get_valid():
    with open('RE_TRAIN/train1.txt', 'r', encoding='utf-8') as f:
        lines = f.readlines()
    data = []
    split_data = {}
    train_data = []
    valid_data = []
    for line in lines:
        jn_data = json.loads(line)
        if jn_data['relation'] not in split_data:
            split_data[jn_data['relation']] = []
        split_data[jn_data['relation']].append(jn_data)
    for key in split_data:
        train_data += split_data[key][0:int(len(split_data[key])*0.75)]
        valid_data += split_data[key][int(len(split_data[key])*0.75):]
        # data.append(jn_data)
    # shuffle_index = [i for i in range(len(data))]
    # random.shuffle(shuffle_index)
    # valid_idnex = shuffle_index[0:int(len(data)*0.25)]
    # train_index = shuffle_index[int(len(data)*0.25):]
    # valid_data = [data[i] for i in valid_idnex]
    # train_data = [data[i] for i in train_index]
    train = open('RE_TRAIN/train.txt', 'w', encoding='utf-8')
    valid = open('RE_TRAIN/valid.txt', 'w', encoding='utf-8')
    for item in train_data:
        train.write(json.dumps(item, ensure_ascii=False) + '\n')
    for item in valid_data:
        valid.write(json.dumps(item, ensure_ascii=False) + '\n')
    train.close()
    valid.close()

def strong_data1():
    with open('RE_TRAIN/train1.txt', 'r', encoding='utf-8') as f:
        lines = f.readlines()
    data = []
    for line in lines:
        jn_data = json.loads(line)
        if jn_data['relation'] == '亲属关系':
            data.append(jn_data)
    print(data)
    shuffle_index = [i for i in range(len(data))]
    random.shuffle(shuffle_index)
    shuffle_data = [data[i] for i in shuffle_index]
    ndata = []
    for e in shuffle_data:
        h = e['h']['pos']
        h_name = e['h']['name']
        t = e['t']['pos']
        t_name = e['t']['name']
        text = e['text']
        relation = e['relation']
        try:
            text = text[h[0]:t[1]]
        except:
            continue
        new_h = [0, len(h_name)]
        new_t = [len(text) - len(t_name), len(text)]
        item = {'text': text, 'h': {'name': h_name, 'pos': new_h}, 't': {'name': t_name, 'pos': new_t},
                'relation': relation}
        ndata.append(item)
    print(ndata)
    train = open('./qing.txt', 'w', encoding='utf-8')
    for item in ndata:
        train.write(json.dumps(item, ensure_ascii=False) + '\n')
    train.close()

# get_data()
# strong_data()
# strong_data1()
get_valid()