# @time:2022/11/10 16:13
# @functional:
import untils.DataBase as db
import pandas
import json

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
#     print(pd)
#     return pd
#
# def get_entity():
#     pd = get_entities()
#     group = pd.groupby('entity')
#     entity_weight = []
#     for key, value in group:
#         weight = (
#             key,
#             len(value),
#             value['type'].iloc[0],
#             "NONE",
#             str(list(set(value['_id'].tolist()))),
#         )
#         entity_weight.append(weight)
#     conn, cursor = db.create_lit_obj()
#     cursor.executemany("INSERT INTO entityMsg VALUES (?,?,?,?,?)", entity_weight)
#     conn.commit()
#     print(entity_weight)

# get_entity()