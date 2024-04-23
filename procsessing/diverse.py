# -*- coding = utf-8 -*-
# @Time:
# @Author: GH
import json
import os
import random
from itertools import tee

import requests
import pandas
from untils.PathManger import get_root_path
from untils.DataBase import open_collection, insert_data
import untils.DataBase as db


def getTitle(jsonfile):
    if os.path.exists(jsonfile):
        with open(jsonfile, 'r', encoding='utf8') as fp:
            data = json.load(fp)
        title = []
        for item in data:
            title.append({item['title']: item['author']})
        root_path = get_root_path()
        title_file = os.path.join(root_path, 'source/title.json')
        with open(title_file, 'w', encoding='utf-8') as fp:
            json.dump(title, fp, ensure_ascii=False, indent=4)
    else:
        raise Exception("文件不存在！！！！")



# if __name__ == '__main__':
#     queue_sam()

# def p_process(json_data, filedname):
#     data = main.generate_poetry_prediction_json(json_data, filedname, predictor)
#     return data


# pool = mp.Pool(processes=5)
# jsons = []
# file = open("../source/guwen0-1000.json", 'r', encoding='utf8')
# for line in file:
#     jsons.append(json.loads(line))
# print(jsons)
def split_content(con):
    con = con.split('\n')
    counts = con.count('')
    for i in range(counts):
        con.remove("")
    for j in range(len(con)):
        con[j] = con[j].strip()
    return con


# josn_data = []
# i = 0
# with open("../source/guwen.json", 'r', encoding='utf8') as fp:
#     data = json.load(fp)
#     for item in data:
#         new_item = {'_id': i, 'title': item['title'], 'author': item['writer']}
#         content = split_content(item['content'])
#         new_item['paragraphs'] = content
#         if 'translation' in item.keys():
#             new_item['translation'] = split_content(item['translation'])
#         else:
#             new_item['translation'] = []
#         josn_data.append(new_item)
#         i += 1
# with open("../source/guwen1.json", 'w', encoding='utf8') as fp:
#     json.dump(josn_data, fp, ensure_ascii=False, indent=4)

# coll = db.open_collection('POEMDATA', 'poem')
# data_json = []
# for item in coll.find():
#     if len(item["entitys"])>0:
#         for i in range(len(item["entitys"])):
#             item_josn = []
#             item_josn.append(item['_id'])
#             item_josn.append(item["entitys"][i])
#             pos = item['labels_pos'][i]
#             try:
#                 type = item['labels'][pos[0]][pos[1]]
#             except IndexError:
#                 type = 'unkonw'
#             item_josn.append(type)
#             data_json.append(item_josn)
#
#
# pd = pandas.DataFrame(data_json,columns=['_id', 'entity', 'type'])
# group = pd.groupby('entity')
# entity_weight = []
# for key, value in group:
#     weight = {
#         "name": key,
#         "value": len(value),
#         "ids": value['_id'].tolist(),
#         "etype":value['type'].iloc[0]
#     }
#     entity_weight.append(weight)

def geocoding(place_name):
    url = r"https://restapi.amap.com/v3/geocode/geo?"
    param = {
        'key': "9ded1192a79c33ec88730000cd408f7e",
        'address': '|'.join(place_name),
        'batch': True
    }
    location = []
    res = requests.get(url, params=param)
    try:
        res_josn = res.json()
        print(res_josn)
        geocodes = res_josn['geocodes']
        for i in range(len(place_name)):
            name = place_name[i]
            value = geocodes[i]['location']
            if value:
                value = [float(item) for item in ''.join(value).split(',')]
            else:
                value = []
            location.append({'name': name,
                             'value': value})
        return location
    except KeyError:
        return []

def get_entities():
    coll = db.open_collection('POEMDATA', 'poem')
    data_json = []
    for item in coll.find():
        if len(item["entitys"]) > 0:
            for i in range(len(item["entitys"])):
                item_josn = []
                item_josn.append(item['_id'])
                item_josn.append(item["entitys"][i])
                pos = item['labels_pos'][i]
                try:
                    type = item['labels'][pos[0]][pos[1]]
                except IndexError:
                    type = 'unkonw'
                item_josn.append(type)
                data_json.append(item_josn)

    pd = pandas.DataFrame(data_json, columns=['_id', 'entity', 'type'])
    return pd


# pd = get_entities()
# group = pd.groupby('type')
# points = []
# for key, value in group:
#     if key == 'B-LOC':
#         p_group = value.groupby('entity')
#         groups = p_group.groups
#         keys = list(p_group.groups.keys())
#         for i in range(0, len(keys), 10):
#             if (i+10) < len(keys):
#                 curKey = keys[i:i+10]
#             else:
#                 curKey = keys[i:-1]
#             res = geocoding(curKey)
#             for p in res:
#                 indexs = groups[p['name']]
#                 ids = [pd.iloc[index, 0].item() for index in indexs]
#                 p['value'].append(len(indexs))
#                 p['ids'] = ids
#             points += res
#     break
#     continue
# with open("../source/palces.json", 'w', encoding='utf8') as fp:
#     json.dump(points, fp, ensure_ascii=False, indent=4)


# 获取关系
# coll = db.open_collection('POEMDATA', 'poem')
# pd = get_entities()
# poem_data = coll.find()
# persons = []
# for item in poem_data:
#     persons.append(item['author'])
#
# group = pd.groupby('type')
# for key, value in group:
#     if key == 'B-PER':
#         # 创建点
#         persons += value['entity'].tolist()
#         nodes = sorted(set(persons), key=persons.index)
#         nodes = [{'name': nodes[i], nodes[i]:i} for i in range(len(nodes))]
#
#         # 构造边
#         eages = []
#         ids = value['_id']
#         id_group = value.groupby('_id')
#         ids = list(id_group.groups.keys())
#         groups = id_group.groups
#         for id in ids:
#             author = coll.find({'_id': id})[0]['author']
#             indexs = groups[id]
#             person = [pd.iloc[index, 1] for index in indexs]
#             person = sorted(set(person), key=person.index)
#
#         break


#json数据文件预处理
def processing_data():
    coll = db.open_collection('POEMDATA', 'poem')
    path = r'E:/src/数据集/chinese-gushiwen-master/guwen/'
    json_data = []
    try:
        poem_id = len(coll.find().distinct("_id"))
    except ValueError:
        poem_id = 0
    files = os.listdir(path)  # 得到文件夹下的所有文件名称
    error = 0
    oversize = 0
    for file in files[1:-1]:
        filepath = os.path.join(path, file)
        fp = open(filepath, 'r', encoding='utf8')
        lines = fp.readlines()
        for line in lines:
            line = json.loads(line)
            try:
                if len(line['content']) > 512:
                    oversize += 1
                    continue
                content = line['content'].split('\n')
                translation = line['translation'].split('\n')
                content = [i for i in content if i != '']
                translation = [i for i in translation if i != '']
                line_data = {
                    '_id': poem_id,
                    'title': line['title'],
                    'author': line['writer'],
                    'paragraphs': [sentence.strip() for sentence in content],
                    'translation': [tsen.strip() for tsen in translation],
                    'dynasty': line['dynasty']
                }
                json_data.append(line_data)
                poem_id += 1
            except KeyError:
                error += 1
                continue
    with open('../source/guwen2.json', 'w', encoding='utf8') as fp:
        json.dump(json_data, fp, ensure_ascii=False, indent=4)


def insert_dynasty():
    coll = db.open_collection('POEMDATA', 'poem')
    fp = open(r'../source/guwen0-1000.json', 'r', encoding='utf8')
    lines = fp.readlines()
    for i in range(len(lines)):
        line = json.loads(lines[i])
        title = coll.find({'_id': i})[0]['title']
        if title == line['title']:
            coll.update_one({'_id': i}, {'$set': {'dynasty': line['dynasty']}})





# datapro()
# processing_data()

def extract_tree():
    coll = db.open_collection('POEMDATA', 'poem')
    collections = coll.find()
    data = {"name": "flare", "children": []}
    temp_data = []
    for item in collections:
        temp_data.append([item["dynasty"], item['author'], item['_id'], item['title']])
    pd = pandas.DataFrame(temp_data, columns=['dynasty', 'author', '_id', 'title'])
    dy_group = pd.groupby("dynasty")
    for key, value in dy_group:
        poets = []
        poet_group = value.groupby('author')
        for p_key, p_value in poet_group:
            poets.append({
                'name': p_key,
                'children': [{'name': poem, 'ids': id} for poem, id in zip(p_value['title'], p_value['_id'])],
                'ids': [p_id for p_id in p_value['_id']]
            })
        data['children'].append({
            'name': key,
            'children': poets,
            'ids': [d_id for d_id in value['_id']]
        })

    print(data)
    # danastys = set([item['dynasty'] for item in collections])
    # poets = set([{item['author']:item['dynasty']} for item in collections])
    # for dynasty in danastys:
    #     dynasty = {
    #         'name': dynasty,
    #         'children': []
    #     }
    #     data['children'].append(dynasty)
    # for item in collections:
    #     dynasty = item['dynasty']
    #     for d in data['children']:
    #         if dynasty == d['name']:
    #             d['children']
    # dynastys = []
    # for item in collections:
    #     exist = False
    #     for dynasty in dynastys:
    #         if item['dynasty'] == dynasty['name']:
    #             dynasty['ids'].append(item["_id"])
    #             exist = True
    #             break
    #     if not exist:
    #         dynastys.append({
    #             'name': item['dynasty'],
    #             'children': [],
    #             'ids': [item['_id']]
    #         })
    # for data in dynastys:
    #     poets = []
    #     ids = data['ids']
    #     for id in ids:
    #         poem = coll.find({"_id": id})
    #         if poem not in poets:


# def get_place():
#     pd = get_entities()
#     group = pd.groupby('type')
#     points = []
#     for key, value in group:
#         if key == 'B-LOC':
#             p_group = value.groupby('entity')
#             groups = p_group.groups
#             keys = list(p_group.groups.keys())
#             for i in range(0, len(keys), 10):
#                 if (i + 10) < len(keys):
#                     curKey = keys[i:i + 10]
#                 else:
#                     curKey = keys[i:-1]
#                 res = geocoding(curKey)
#                 for p in res:
#                     indexs = groups[p['name']]
#                     ids = [pd.iloc[index, 0].item() for index in indexs]
#                     p['value'].append(len(indexs))
#                     p['ids'] = ids
#                 points += res
#         continue
#
#
# def getRelation():
#     coll = db.open_collection('POEMDATA', 'poem')
#     reocrds = coll.find()
#     all_per = []
#     temp = []
#     for item in reocrds:
#         all_per.append(item['dynasty']+'-'+item['author'])
#         per_entity = db.getEntityType(item, 'B-PER')
#         temp += per_entity
#     all_per = list(set(all_per))
#     temp = list(set(temp))
#     # 构造查询
#     au_query = {}
#     po_query = {}
#     for i in range(len(all_per)):
#         au_query[f'{all_per[i]}'] = i
#     nodes = [{'name': item.split('-')[1], item.split('-')[1]:au_query[item]} for item in au_query]
#     for i in range(len(temp)):
#         po_query[f'{temp[i]}'] = i + len(all_per)
#     # 点
#     nodes += [{'name': item, item: po_query[item]} for item in po_query]
#     # 边
#     eages = []
#     reocrds = coll.find()
#     for item in reocrds:
#         pre_entity = db.getEntityType(item, 'B-PER')
#         per_entity = list(set(pre_entity))
#         source = au_query[item['dynasty']+'-'+item['author']]
#         eages += [{'source': source, 'target': po_query[target], 'relation': item['title'], 'value':1} for target in per_entity]
#     print(eages)
#
#
# getRelation()
# def getRlation():
#     show_dynasty = '唐代'
#     coll = db.open_collection('POEMDATA', 'poem')
#     pd = []
#     for item in coll.find():
#         ety = db.getEntityType(item, 'B-PER')
#         if ety is None or ety == []:
#             continue
#         pd.append([item['_id'], item['title'], item['dynasty'], item['author'], ety])
#     pd = pandas.DataFrame(pd, columns=['_id', 'title', 'dynasty', 'author', 'entity'])
#     au_query, po_query, ti_query, pd = create_query_dic(pd, show_dynasty)
#     # print(pd)
#     if len(au_query) == 0 or len(po_query) == 0:
#         return {
#             'err_msg': '未获取查询信息，检查是否存在该朝代'
#         }
#     # 构造点
#     nodes = [{'name': item, item: au_query[item]['id'], 'ids': au_query[item]['poemID']}
#              for item in au_query]
#     nodes += [{'name': item, item: po_query[item]['id'], 'ids': po_query[item]['poemID']}
#               for item in po_query]
#     nodes += [{'name': item, item: ti_query[item]['id'], 'ids': ti_query[item]['poemID']} for item in ti_query]
#
#     eages = []
#     # 构造边
#     # 作者---诗
#     for item in au_query.items():
#         for title in item[1]['poems']:
#             target = ti_query[f'{title}-{item[0]}']['id']
#             eages += [{'source': au_query[item[0]]['id'],
#                        'target':target,
#                        'relation':'著',
#                        'value':random.randint(1, 5)}]
#
#     for index, row in pd.iterrows():
#         per_eny = list(set(row['entity']))
#         title = [ti_query[f"{po_query[item]['poem']}-{po_query[item]['author']}"]['id'] for item in per_eny]
#         print(len(per_eny), len(title))
#         links = zip(per_eny, title)
#         eages += [{'source': t_id,
#                    'target': po_query[per]['id'],
#                    'relation':'涉及',
#                    'value':random.randint(1, 5)} for per, t_id in links]
#
#     eages = json.dumps(eages, ensure_ascii=False, indent=4)
#     nodes = json.dumps(nodes, ensure_ascii=False, indent=4)


# def create_query_dic(pd, show_dynasty):
#     dy_group = pd.groupby('dynasty')
#     au_query = {}
#     po_query = {}
#     ti_query = {}
#     au_id = 0
#     cur_dynasty_pd = None
#     if show_dynasty == 'all':
#         cur_dynasty_pd = pd
#     # 构造查询：作者查询字典
#     for key, value in dy_group:
#         if key != show_dynasty and show_dynasty != 'all':
#             continue
#         if show_dynasty != 'all':
#             cur_dynasty_pd = value
#         au_group = value.groupby('author')
#         for auk, auv in au_group:
#             au_query[auk] = {'id': au_id, 'poemID': auv['_id'].tolist(), 'poems': auv['title'].tolist()}
#             au_id += 1
#     # 构造查询：诗中人物查询字典
#     po_zip = zip(cur_dynasty_pd['_id'].tolist(), cur_dynasty_pd['entity'].tolist(), cur_dynasty_pd['title'].tolist(),
#                  cur_dynasty_pd['author'].tolist())
#     init_zip, md_zip = tee(po_zip)
#     # 初始化字典
#     for _id, eny, title, author in init_zip:
#         for item in eny:
#             po_query[item] = {'id': 0, 'poemID': [], 'poem': title, 'author': author}
#     # 写入人物对应的诗的id
#     for _id, eny, title, author in md_zip:
#         for item in eny:
#             if _id not in po_query[item]['poemID']:
#                 po_query[item]['poemID'].append(_id)
#     # 写入查询id
#     for item in po_query:
#         po_query[item]['id'] = au_id
#         au_id += 1
#
#     for index, row in cur_dynasty_pd.iterrows():
#         ti_query[f"{row['title']}-{row['author']}"] = {'id': au_id, 'poemID': row['_id']}
#         au_id += 1
#     return au_query, po_query, ti_query, cur_dynasty_pd


# def get_model_config():
#     root = get_root_path()
#     model_config = os.path.join(root, 'model/model.json')
#     with open(model_config, 'r', encoding='utf8') as fp:
#         json_data = json.load(fp)
#     print(json_data)


# get_model_config()
def getRlation():
    show_dynasty = '唐代'
    coll = db.open_collection('POEMDATA', 'poem')
    pd = []
    for item in coll.find():
        ety = db.getEntityType(item, 'B-PER')
        if ety is None or ety == []:
            continue
        pd.append([item['_id'], item['title'], item['dynasty'], item['author'], ety])
    pd = pandas.DataFrame(pd, columns=['_id', 'title', 'dynasty', 'author', 'entity'])
    au_query, po_query, ti_query, pd = create_query_dic(pd, show_dynasty)
    # print(pd)
    # 构造点
    nodes = [{'name': item, item: au_query[item]['id'], 'ids': au_query[item]['poemID']}
             for item in au_query]
    nodes += [{'name': item.split('-')[0], item: ti_query[item]['id'], 'ids': ti_query[item]['poemID']} for item in ti_query]
    nodes += [{'name': item, item: po_query[item]['id'], 'ids': po_query[item]['poemID']}
              for item in po_query]

    eages = []
    # 构造边
    # 作者---诗
    for item in au_query.items():
        for title in item[1]['poems']:
            target = ti_query[f'{title}-{item[0]}']['id']
            eages += [{'source': au_query[item[0]]['id'],
                       'target': target,
                       'relation': '著',
                       'value': 2}]

    for index, row in pd.iterrows():
        per_eny = list(set(row['entity']))
        title = [ti_query[f"{po_query[item]['poem']}-{po_query[item]['author']}"]['id'] for item in per_eny]
        links = zip(per_eny, title)
        eages += [{'source': t_id,
                   'target': po_query[per]['id'],
                   'relation': '涉及',
                   'value': 2} for per, t_id in links]


def create_query_dic(pd, show_dynasty):
    dy_group = pd.groupby('dynasty')
    au_query = {}
    po_query = {}
    ti_query = {}
    au_id = 0
    cur_dynasty_pd = None
    if show_dynasty == 'all':
        cur_dynasty_pd = pd
    # 构造查询：作者查询字典
    for key, value in dy_group:
        if key != show_dynasty and show_dynasty != 'all':
            continue
        if show_dynasty != 'all':
            cur_dynasty_pd = value
        au_group = value.groupby('author')
        for auk, auv in au_group:
            au_query[auk] = {'id': au_id, 'poemID': auv['_id'].tolist(), 'poems': auv['title'].tolist()}
            au_id += 1

    # 构造诗名查询字典
    print(f'{au_id}:{len(au_group)}')
    for index, row in cur_dynasty_pd.iterrows():
        ti_query[f"{row['title']}-{row['author']}"] = {'id': 0, 'poemID': list(row['_id'])}
    for item in ti_query:
        ti_query[item]['id'] = au_id
        au_id += 1
    print(f'{au_id}:{len(ti_query)}')
    # 构造查询：诗中人物查询字典
    po_zip = zip(cur_dynasty_pd['_id'].tolist(), cur_dynasty_pd['entity'].tolist(), cur_dynasty_pd['title'].tolist(),
                 cur_dynasty_pd['author'].tolist())
    init_zip, md_zip = tee(po_zip)
    # 初始化字典
    for _id, eny, title, author in init_zip:
        for item in eny:
            po_query[item] = {'id': 0, 'poemID': [], 'poem': title, 'author': author}
    # 写入人物对应的诗的id
    for _id, eny, title, author in md_zip:
        for item in eny:
            if _id not in po_query[item]['poemID']:
                po_query[item]['poemID'].append(_id)
    # 写入查询id
    for item in po_query:
        po_query[item]['id'] = au_id
        au_id += 1
    print(f"{au_id}:{len(po_query)}")
    return au_query, po_query, ti_query, cur_dynasty_pd


# getRlation()

# from model.model import Self_Attention_Layer
# import tensorflow as tf
#
#
# x = tf.ones((2, 5, 10))
# att = Self_Attention_Layer()
# y = att(x, [5, 5])
# print(y.shape)
# print(y)
