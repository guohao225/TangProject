# @time:2023/5/3 20:55
# @functional:
import json
import random

from model.Recorder import recorder
from al_api.active_learing import AL
from untils import DataBase as db

def insert_oper_record(data):
    try:
        for item in data:
            db.insert_oper_record(item)
        return 1
    except:
        return 0

def query_operation_record_sample(data):
    type1 = []
    type2 = []
    type3 = []
    for item in data:
        if item[3] == 0:
            type1.append(item)
        elif item[3] == 1:
            type2.append(item)
        else:
            type3.append(item)
    roc = []
    add = {'type':0, 'data':[item[7] for item in type1],
           'msg':[[s for s in item] for item in type1]}
    o_chg = {'type': 1, 'data': [f"{item[6]} to {item[7]}" for item in type2],
             'msg':[[s for s in item] for item in type2]}
    o_del= {'type': 2, 'data': [item[6] for item in type3],
             'msg':[[s for s in item] for item in type3]}
    if len(add['data']) > 0:
        roc.append(add)
    if len(o_chg['data'])> 0:
        roc.append(o_chg)
    if len(o_del['data'])> 0:
        roc.append(o_del)
    return roc

def query_record_sample(id , loop):
    data = db.query_operation(id, loop)
    roc = query_operation_record_sample(data)
    return roc

def query_record_loop(loop):
    data = db.query_operation(loop=loop)
    roc = query_operation_record_sample(data)
    return roc


    # for key in loop.keys():
    #     for item in loop[key]['']
    #     recorder.add_operation(key, loop[key]['data'])
    # print(recorder.operating_record)
