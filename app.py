# # -*- coding = utf-8 -*-
# # @Time:
# # @Author: GH
# import os
# from itertools import tee
# import requests
# from flask import Flask, request, jsonify, send_file
# from flask_cors import CORS, cross_origin
# from tqdm import tqdm
#
# import main
# from untils import DataBase as db
# import untils.Constant as Const
# import json
# import pandas
# from concurrent.futures import ThreadPoolExecutor
# from al_api import query, setting
# import al_api.query as api
# import al_api.dataProcess as dp
# from untils import DictMaper
#
# executer = ThreadPoolExecutor()
# app = Flask(__name__)
#
# places = []
# startProcess = False
# app.config['JSON_AS_ASCII'] = False
# ner_model = main.create_model(main.configure.generate_checkpoints_name()[1])
#
#
# PROCESS_NUM = 0
# POEM_TOTAL = -1
#
# @app.route('/get_message', methods=['GET', 'POST'])
# @cross_origin()
# def get_message():
#     coll = db.open_collection('POEMDATA', 'poem')
#     try:
#         all_poem = len(coll.find().distinct("_id"))
#     except ValueError:
#         all_poem = 0
#     return {
#         'poem_num': all_poem,
#     }
#
#
# @app.route('/get_model_config', methods=['GET', 'POST'])
# @cross_origin()
# def get_model_config():
#     config = setting.get_model_config()
#     return {
#         'res': config
#     }
#
#
# @app.route('/set_model_config', methods=['GET', 'POST'])
# @cross_origin()
# def set_model_config():
#     data = request.get_json()['data']
#     res = setting.set_model_config(data)
#     return {
#         'res': res
#     }
#
#
# @app.route('/reset_model_config', methods=['GET', 'POST'])
# @cross_origin()
# def reset_model_config():
#     setting.reset_model_config()
#     return {
#         'res': ""
#     }
#
# @app.route('/uncertainty', methods=['GET', 'POST'])
# @cross_origin()
# def uncertainty():
#     sentence = request.get_json()['sentence']
#     data = main.predict(sentence, ner_model)
#     return {
#         "res": data
#     }
#
# @app.route('/origin_data', methods=['GET', 'POST'])
# @cross_origin()
# def origin_data():
#     global PROCESS_NUM
#     global POEM_TOTAL
#     data = request.get_json()['json']
#     POEM_TOTAL = len(data)
#     fieldname = request.get_json()['name']
#     coll = db.open_collection('POEMDATA', 'poem')
#     id = coll.count_documents({})
#     temp = {}
#     with tqdm(data) as log:
#         for item in data:
#             temp['_id'] = id
#             temp['paragraphs'] = item[fieldname['poem']]
#             temp['title'] = item[fieldname['title']]
#             temp['author'] = item[fieldname['author']]
#             temp['translation'] = []
#             main.predict_poem(temp, temp['paragraphs'], ner_model)
#             db.insert_data(coll, temp)
#             PROCESS_NUM += 1
#             log.update(1)
#             log.set_postfix({"staus": f'已处理:{PROCESS_NUM}首'})
#             id+=1
#         # print(f'已处理{item["_id"]}首诗')
#     PROCESS_NUM = 0
#     POEM_TOTAL = -1
#     return {
#         'res': 1
#     }
#
#
# @app.route('/get_process_info', methods=['GET', 'POST'])
# @cross_origin()
# def get_process_info():
#     return {
#         "res":{
#             "processed": PROCESS_NUM,
#             "total": POEM_TOTAL
#         }
#     }
#
# # 爬虫爬取词语解释
# @app.route('/query_word', methods=['GET', 'POST'])
# @cross_origin()
# def query_word():
#     word = request.get_json()['word']
#     if word == {}:
#         return
#     content = api.word_query(word)
#     return jsonify(res=str(content))
#
#
# @app.route('/get_poem', methods=['GET', 'POST'])
# @cross_origin()
# def get_poem():
#     query = request.get_json()['query']
#     value = request.get_json()['value']
#     coll = db.open_collection('POEMDATA', 'poem')
#     res = None
#     if query == '_id':
#         res = coll.find({'_id': int(value)})
#     elif query == 'title':
#         res = coll.find({'title': value})
#     elif query == 'entitys':
#         res = coll.find({Const.ENTITIES: value})
#     elif query == 'ids':
#         res = db.find_many(value, coll)
#     elif query == 'dynasty':
#         res = coll.find({'dynasty': value})
#     elif query == 'poem':
#         res = coll.find({'poem': value})
#     elif query == 'author':
#         res = coll.find({query: value})
#     if res is None:
#         return {
#             'res': []
#         }
#     p_data = [data for data in res]
#     entity_msgs = []
#     for item in p_data:
#         entytiys = [db.find_entity(e) for e in item['entitys']]
#         entity_msg = [{"text": item[0], 'num':item[1], 'type':item[2]} for item in entytiys]
#         entity_msgs.append(entity_msg)
#     return {
#         "res": p_data,
#         "msg": entity_msgs
#     }
#
#
# @app.route('/check_db_con', methods=['GET', 'POST'])
# @cross_origin()
# def check_db_con():
#     return {
#         "result": db.collection_is_exist('POEMDATA', 'poem')
#     }
#
#
# @app.route('/update', methods=['GET', 'POST'])
# @cross_origin()
# def update():
#     data = request.get_json()
#     coll = db.open_collection('POEMDATA', 'poem')
#     update_data = {
#         Const.LABELS: data['labels'],
#         Const.LABELS_POS: data['entity_pos'],
#         Const.ENTITIES: data['entitys']
#     }
#     res = db.update_data_by_id(data['id'], update_data, coll)
#     if res.modified_count > 0:
#         return {'res': True}
#     return {'res': False}
#
#
# @app.route('/get_entity', methods=['GET', 'POST'])
# @cross_origin()
# def get_entity():
#     pd = get_entities()
#     group = pd.groupby('entity')
#     entity_weight = []
#     for key, value in group:
#         weight = {
#             "name": key,
#             "value": len(value),
#             "ids": value['_id'].tolist(),
#             "etype": value['type'].iloc[0]
#         }
#         entity_weight.append(weight)
#
#     return {
#         'data': entity_weight
#     }
#
#
# @app.route('/get_person', methods=['GET', 'POST'])
# @cross_origin()
# def get_person():
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
#     if len(au_query) == 0 or len(po_query) == 0:
#         return {
#             'err_msg': '未获取查询信息，检查是否存在该朝代'
#         }
#     # 构造点
#     nodes = [{'name': item, item: au_query[item]['id'], 'ids': au_query[item]['poemID'], "type": au_query[item]["type"]}
#              for item in au_query]
#     nodes += [{'name': item.split('-')[0], item: ti_query[item]['id'], 'ids': ti_query[item]['poemID'],
#                "type": ti_query[item]["type"]} for item in ti_query]
#     nodes += [
#         {'name': item, item: po_query[item]['id'], 'ids': po_query[item]['poemID'], "type": po_query[item]['type']}
#         for item in po_query]
#
#     eages = []
#     # 构造边
#     # 作者---诗
#     for item in au_query.items():
#         for title in item[1]['poems']:
#             target = ti_query[f'{title}-{item[0]}']['id']
#             eages += [{'source': au_query[item[0]]['id'],
#                        'target': target,
#                        'relation': '著',
#                        'value': 2}]
#
#     for index, row in pd.iterrows():
#         per_eny = list(set(row['entity']))
#         title = [ti_query[f"{po_query[item]['poem']}-{po_query[item]['author']}"]['id'] for item in per_eny]
#         links = zip(per_eny, title)
#         eages += [{'source': t_id,
#                    'target': po_query[per]['id'],
#                    'relation': '涉及',
#                    'value': 2} for per, t_id in links]
#
#     eages = json.dumps(eages, ensure_ascii=False, indent=4)
#     nodes = json.dumps(nodes, ensure_ascii=False, indent=4)
#     return jsonify({
#         'nodes': nodes,
#         'eages': eages
#     })
#
#
# @app.route('/get_places', methods=['GET', 'POST'])
# @cross_origin()
# def get_places():
#     global places
#     # if not startProcess:
#     #     executer.submit(get_place_process)
#     return {
#         'points': places,
#         # 'status': not_Done
#     }
#
#
# @app.route('/get_all_message', methods=['GET', 'POST'])
# @cross_origin()
# def get_all_message():
#     coll = db.open_collection('POEMDATA', 'poem')
#     collections = coll.find()
#     data = {"name": "flare", "children": []}
#     temp_data = []
#     for item in collections:
#         temp_data.append([item["dynasty"], item['author'], item['_id'], item['title']])
#     pd = pandas.DataFrame(temp_data, columns=['dynasty', 'author', '_id', 'title'])
#     dy_group = pd.groupby("dynasty")
#     for key, value in dy_group:
#         poets = []
#         poet_group = value.groupby('author')
#         for p_key, p_value in poet_group:
#             poets.append({
#                 'name': p_key,
#                 'children': [{'name': poem, 'value': 1, 'ids': id} for poem, id in
#                              zip(p_value['title'], p_value['_id'])],
#                 'ids': [p_id for p_id in p_value['_id']]
#             })
#         data['children'].append({
#             'name': key,
#             'children': poets,
#             'ids': [d_id for d_id in value['_id']]
#         })
#     return {
#         'res': data
#     }
#
# @app.route('/get_baseline_log', methods=['GET', 'POST'])
# @cross_origin()
# def get_baseline_log():
#     x, y = setting.get_baseline_log()
#     return {
#         "x": x,
#         "y": y
#     }
#
# # @app.route('/entity_frequency', methods=['GET', 'POST'])
# # # @cross_origin()
# # # def entity_frequency():
# # #     entitys = query.entity_frequency_antv()
# # #     return {
# # #         "res": entitys
# # #     }
#
# @app.route('/download', methods=['GET', 'POST'])
# @cross_origin()
# def download():
#     if not os.path.isfile("./source/temp/train.txt"):
#         data = db.find()
#         word, label = dp.word_label_corresponding(data)
#         df = pandas.DataFrame({'word':word, 'label':label})
#         df.to_csv('./source/temp/train.txt', header=None, index=None, encoding='utf8', sep=' ')
#     return send_file("./source/temp/train.txt", as_attachment=True)
#
#
# @app.route('/begin_train', methods=['GET', 'POST'])
# @cross_origin()
# def begin_train():
#     status = request.get_json()['status']
#     setting.begin_train(status)
#     return {
#         "res": 1
#     }
#
#
# @app.route('/get_train_data', methods=['GET', 'POST'])
# @cross_origin()
# def get_train_data():
#     x, y = setting.get_train_data()
#     return {
#         "x":x,
#         "y":y
#     }
#
# @app.route('/query_baseline', methods=['GET', 'POST'])
# @cross_origin()
# def query_baseline():
#     query_baseline()
#
# def geocoding(place_name):
#     url = r"https://restapi.amap.com/v3/geocode/geo?"
#     param = {
#         'key': "9ded1192a79c33ec88730000cd408f7e",
#         'address': '|'.join(place_name),
#         'batch': True
#     }
#     location = []
#     res = requests.get(url, params=param)
#     try:
#         res_josn = res.json()
#         print(res_josn)
#         geocodes = res_josn['geocodes']
#         for i in range(len(place_name)):
#             name = place_name[i]
#             value = geocodes[i]['location']
#             if value:
#                 value = [float(item) for item in ''.join(value).split(',')]
#             else:
#                 value = []
#             location.append({'name': name,
#                              'value': value})
#         return location
#     except KeyError:
#         return []
#
# def get_entities():
#     coll = db.open_collection('POEMDATA', 'poem')
#     data_json = []
#     for item in coll.find():
#         if len(item["entitys"]) > 0:
#             for i in range(len(item["entitys"])):
#                 item_josn = []
#                 item_josn.append(item['_id'])
#                 item_josn.append(item["entitys"][i])
#                 pos = item['labels_pos'][i]
#                 try:
#                     type = item['labels'][pos[0]][pos[1]]
#                 except IndexError:
#                     type = 'unkonw'
#                 item_josn.append(type)
#                 data_json.append(item_josn)
#     pd = pandas.DataFrame(data_json, columns=['_id', 'entity', 'type'])
#     return pd
#
# def get_place_process():
#     global places
#     global startProcess
#     startProcess = True
#     pd = get_entities()
#     group = pd.groupby('type')
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
#                 temp_place = []
#                 for p in res:
#                     indexs = groups[p['name']]
#                     ids = [pd.iloc[index, 0].item() for index in indexs]
#                     ids = list(set(ids))
#                     p['ids'] = ids
#                     if not p['value']:
#                         p['value'] = [0, 0]
#                     temp_place.append({
#                         'type': 'Feature',
#                         "geometry": {
#                             "type": 'Point',
#                             "coordinates": p["value"]
#                         },
#                         'properties': {
#                             "size":len(ids),
#                             'description':f'<strong>{p["name"]}</strong>',
#                             "ids":ids,
#                             "name":p['name']
#                         },
#                     })
#                     # else:
#                     #     p['value'].append(len(ids))
#                 places += temp_place
#         continue
#     # is_Done = False
#
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
#             au_query[auk] = {'id': au_id, 'poemID': auv['_id'].tolist(), 'poems': auv['title'].tolist(),
#                              "type": "author"}
#             au_id += 1
#
#     # 构造诗名查询字典
#     for index, row in cur_dynasty_pd.iterrows():
#         ti_query[f"{row['title']}-{row['author']}"] = {'id': 0, 'poemID': [row['_id']], "type": "poem"}
#     for item in ti_query:
#         ti_query[item]['id'] = au_id
#         au_id += 1
#
#     # 构造查询：诗中人物查询字典
#     po_zip = zip(cur_dynasty_pd['_id'].tolist(), cur_dynasty_pd['entity'].tolist(), cur_dynasty_pd['title'].tolist(),
#                  cur_dynasty_pd['author'].tolist())
#     init_zip, md_zip = tee(po_zip)
#     # 初始化字典
#     for _id, eny, title, author in init_zip:
#         for item in eny:
#             po_query[item] = {'id': 0, 'poemID': [], 'poem': title, 'author': author, "type": "entity"}
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
#     return au_query, po_query, ti_query, cur_dynasty_pd
#
#
# if __name__ == '__main__':
#     get_place_process()
#     app.run()
def after_return(callback):
    def decorator(func):
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            callback()
            return result
        return wrapper
    return decorator

# 示例函数
def add_numbers(a, b):
    return a + b

# 回调函数
def print_message():
    print("函数返回后执行回调函数")

# 使用装饰器
@after_return(print_message)
def decorated_add_numbers(a, b):
    return a + b

# 调用函数
result = decorated_add_numbers(3, 4)
print("结果:", result)