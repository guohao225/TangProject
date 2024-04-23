# @time:2023/4/24 10:03
# @functional:
import json
import os
import pandas
from activteLearner import ActiveLearning, DataPool
import tensorflow as tf
from untils import DataBase as db
import untils.evaluate as eva
from untils.Config import CONFIG
from model.Recorder import recorder
from model.NerModel import NerModel, NERMetrics, AtnCallback
import numpy as np

# model = NerModel()
# ## 初始加载模型
# model.load_weights(os.path.join(CONFIG.root_path, f'checkpoints/{CONFIG.save_path}'))
# model.compile(optimizer='adam', loss='sparse_categorical_crossentropy', metrics=[NERMetrics(name='f1')])
# AL = ActiveLearning(model, 10, 'alltangs', 'LC')


# recorder.set_data_info('basedata', 'LC')
def init_al():
    loop = db.find_max_loop(AL.data_pool.data_name)
    AL.loop = loop + 1
    # train_data = db.find_labeled_data(AL.data_pool.data_name)
    # x, y = process_to_train(train_data)
    # print(x)
    # print(y)
    # AL.x_train = x
    # AL.y_train = y

def set_config(config):
    AL.data_pool.data_name = config['data_name']
    AL.data_pool.score_name = config['strategy']
    AL.data_pool.num_sample = config['select_num']
## 第一步：设置参数
def set_parameter(data):
    global AL
    select_num = data['select_num']
    data_name = data['data_name']
    strategy = data['strategy']
    loop = db.find_max_loop(data_name)
    train_data = db.find_labeled_data(AL.data_pool.data_name)
    if AL is not None:
        if AL.data_pool.data_name != data_name:
            AL.data_pool.selected_idx = []
            AL.data_pool.unlabel_pool = []
            AL.data_pool.labeled_pool = []
        # AL.data_pool.selected_idx = []
        AL.data_pool.num_sample = select_num
        AL.data_pool.data_name = data_name
        AL.data_pool.score_name = strategy
    else:
        AL = ActiveLearning(model, select_num, data_name, strategy)
    recorder.data_name = data_name
    recorder.score_name = strategy
    if loop == -1:
        AL.loop = 0
    x, y = process_to_train(train_data)
    AL.x_train = x
    AL.y_train = y


## 第二步：选择样本
def select_samples():
    idx = AL.select_samples()
    loop = AL.loop
    data_list = get_sample_list(idx)
    # 查询样本的具体信息
    samples = db.find_data_by_id(AL.data_pool.data_name, idx)
    ### 解析实体信息
    sample_entities = []
    for item in samples:
        content = "".join(json.loads(item[3]))
        entities = json.loads(item[6])
        if len(entities) > 0:
            entities = [{'id': item[0],
                         'name': content[ent[1]:ent[2] + 1],
                         'score': ent[3],
                         'type': ent[0],
                         'LC': item[7],
                         'MNLP': item[8],
                         'entity_MNLP': item[9],
                         'status': item[10],
                         'size': db.find_frequency(content[ent[1]:ent[2] + 1], AL.data_pool.data_name)
                         } for ent in entities]
        else:
            entities = [{'id': item[0],
                         'name': item[1],
                         'score': 0.5,
                         'type': 'sample',
                         'LC': item[7],
                         'MNLP': item[8],
                         'entity_MNLP': item[9],
                         'status': item[10],
                         'size': 20
                         }]
        sample_entities += entities
    return sample_entities, data_list, loop


def get_sample_list(ids):
    res = db.find_data_list_by_id(AL.data_pool.data_name, ids)
    data_list = []
    for item in res:
        data_list.append({'id': item[0], 'title': item[1], 'LC': item[2], 'MNLP': item[3], 'ENTITY_MNLP': item[4]})
    return data_list


def find_suggest():
    try:
        res = db.find_suggest(AL.data_pool.data_name, AL.data_pool.selected_idx, AL.data_pool.score_name)
        return res
    except:
        return -1


def get_tag_sample(id):
    try:
        res = db.find_data_by_id(AL.data_pool.data_name, [id])[0]
        sample = {'id': res[0],
                  'title': res[1],
                  'author': res[2],
                  'content': "".join(json.loads(res[3])),
                  'label': json.loads(res[4]),
                  'entity': json.loads(res[6])
                  }
        return sample
    except:
        return {}


def tag_update(data, status):
    # try:
    id = data['id']
    label = data['label']
    entitys = eva.extract_entities(label, tf.convert_to_tensor([1 for x in range(len(label))]))
    # 查找当前记录的标注数据
    sample_data = db.find_data_by_id(AL.data_pool.data_name, [id])[0]
    old_label = json.loads(sample_data[4])
    old_entity = json.loads(sample_data[6])
    db.update_data_number(AL.data_pool.data_name, [id], 'status', [status])
    db.update_data_obj(AL.data_pool.data_name, [id], 'label', [label])
    db.update_data_obj(AL.data_pool.data_name, [id], 'entitys', [entitys])
    db.update_data_obj(AL.data_pool.data_name, [id], 'user_label', [old_label])
    db.update_data_obj(AL.data_pool.data_name, [id], 'user_entitys', [old_entity])
    # 添加操作记录
    operation_update(id, AL.loop)
    return 1


# except:
#     return 0
def epoch_tag_down():
    train_data = db.find_lower_loop_data(AL.data_pool.data_name, AL.loop)
    x, y = process_to_train(train_data)
    AL.x_train = x
    AL.y_train = y
    AL.epoch_tag_down()
    if AL.predict:
        sample_entities, data_list, loop = select_samples()
    else:
        sample_entities, data_list, loop = look_loop(AL.loop)
    return sample_entities, data_list, loop


def operation_update(id, loop):
    if AL is None:
        return
    # 获取样本的操作信息
    oper_log = db.query_operation(id, loop)
    if len(oper_log) == 0:
        return
    # 获取样本的score信息
    data = db.find_score_by_sn(AL.data_pool.data_name, AL.data_pool.score_name, [id])
    # size = db.count_sample_record(id, AL.data_pool.score_name)
    if len(data) > 0:
        title, score = data[0]
    else:
        return
    data = {'name': title, 'value': score, 'id': id}
    recorder.add_operation(loop, data)


def query_all():
    data = db.query_operation()
    # 根据loop分类
    loop = {}
    for item in data:
        if item[5] not in loop.keys():
            loop[item[5]] = {}
        if 'data' not in loop[item[5]].keys():
            loop[item[5]]['data'] = []
        loop[item[5]]['data'].append(item[4])
    for key in loop.keys():
        loop[key]['data'] = list(set(loop[key]['data']))
        for item in loop[key]['data']:
            operation_update(item, key)


## 查找所有样本
def find_all_samples():
    if AL is None:
        return {}
    all_samples = db.find_data_list(AL.data_pool.data_name)
    PER = []
    LOC = []
    TIME = []
    res = []
    for item in all_samples:
        tem = {'name': item[1], 'clarity': "", 'score': item[7 if AL.data_pool.score_name == 'LC' else 8],
               'id': item[0], 'weight': 0, 'sen_len': len("".join(json.loads(item[3])))}
        if item[10] == 2:
            tem['clarity'] = 'labeled'
        elif item[14] == 1 and item[10] != 2:
            tem['clarity'] = 'selected'
        else:
            tem['clarity'] = 'unlabel'
        tem['weight'] = len(json.loads(item[6]))
        PER += [e for e in json.loads(item[6]) if e[0] == 'PER']
        LOC += [e for e in json.loads(item[6]) if e[0] == 'LOC']
        TIME += [e for e in json.loads(item[6]) if e[0] == 'ORG']
        res.append(tem)
    return {'sample': res, 'entity': [len(PER), len(LOC), len(TIME)]}


def get_train_record():
    if AL is None:
        return [], []
    res = db.get_all_record()
    record = []
    entity_record = []
    for epoch, train_log, ids, name in res:
        # 折线图数据
        train_log = json.loads(train_log)
        ids = json.loads(ids)
        y = sum(obj['score'] for obj in train_log)
        y = y / len(train_log) if len(train_log) > 0 else y
        f1 = [{'x': item['epoch'], 'y': item['score']} for item in train_log]
        loss = [{'x': item['epoch'], 'y': item['loss']} for item in train_log]
        record.append({
            'x': epoch,
            'y': y,
            'child': f1,
            'loss': loss,
            'ids': ids
        })
        # 柱状图数据
        source_data = db.find_data_by_id(name, ids)
        temp = {'p': 0, 'ap': 0, 'l': 0, 'al': 0, 't': 0, 'at': 0}
        for sample in source_data:
            entity = json.loads(sample[6])
            PER = [item for item in entity if item[0] == 'PER']
            LOC = [item for item in entity if item[0] == 'LOC']
            TIME = [item for item in entity if item[0] == 'ORG']
            old_entity = sample[12]
            if old_entity is not None:
                old_entity = json.loads(old_entity)
                O_PER = [item for item in old_entity if item[0] == 'PER']
                O_LOC = [item for item in old_entity if item[0] == 'LOC']
                O_TIME = [item for item in old_entity if item[0] == 'ORG']
            else:
                O_PER = []
                O_LOC = []
                O_TIME = []
            temp['p'] += len(PER)
            temp['ap'] += len(O_PER)
            temp['l'] += len(LOC)
            temp['al'] += len(O_LOC)
            temp['t'] += len(TIME)
            temp['at'] += len(O_TIME)
        entity_record.append(temp)
    return record, entity_record


def find_loop_entity():
    # if AL is None:
    #     return []
    data = db.find_all_loop_entity(AL.data_pool.data_name)
    ## 先按照轮次分类
    loopdict = {}
    res = []
    for item in data:
        if item[0] not in loopdict.keys():
            loopdict[item[0]] = []
        loopdict[item[0]].append(item)
    for key in loopdict.keys():
        temp = {'date': key, 'words': {'person': [], 'location': [], 'time': []}}
        for item in loopdict[key]:
            entitys = json.loads(item[2])
            content = "".join(json.loads(item[3]))
            temp['words']['person'] += [{'text': content[e[1]:e[2] + 1],
                                         "frequency": db.find_frequency(content[e[1]:e[2] + 1]),
                                         'topic': 'person',
                                         'id': f"{content[e[1]:e[2] + 1]}_{e[1]}_{e[2]}#{item[0]}#{item[1]}",
                                         'sudden': db.find_frequency(content[e[1]:e[2] + 1]) + 1
                                         }
                                        for e in entitys if e[0] == 'PER']
            temp['words']['location'] += [{'text': content[e[1]:e[2] + 1],
                                           "frequency": db.find_frequency(content[e[1]:e[2] + 1]),
                                           'topic': 'location',
                                           'id': f"{content[e[1]:e[2] + 1]}_{e[1]}_{e[2]}#{item[0]}#{item[1]}",
                                           'sudden': db.find_frequency(content[e[1]:e[2] + 1]) + 1
                                           }
                                          for e in entitys if e[0] == 'LOC']
            temp['words']['time'] += [{'text': content[e[1]:e[2] + 1],
                                       "frequency": db.find_frequency(content[e[1]:e[2] + 1]),
                                       'topic': 'time',
                                       'id': f"{content[e[1]:e[2] + 1]}_{e[1]}_{e[2]}#{item[0]}#{item[1]}",
                                       'sudden': db.find_frequency(content[e[1]:e[2] + 1]) + 1
                                       }
                                      for e in entitys if e[0] == 'ORG']
        temp['words']['person'] = grpup_data(temp['words']['person'], 'text')
        temp['words']['location'] = grpup_data(temp['words']['location'], 'text')
        temp['words']['time'] = grpup_data(temp['words']['time'], 'text')
        res.append(temp)
    return res


def grpup_data(data, key):
    grouped_data = {}
    # 遍历每个JSON对象
    for item in data:
        # 获取城市信息
        city = item[key]
        # 将对象添加到相应的城市分组中
        if city in grouped_data:
            grouped_data[city].append(item)
        else:
            grouped_data[city] = [item]
    res = []
    for item in grouped_data:
        res.append({
            "text": item,
            "frequency": len(grouped_data[item]),
            "topic": grouped_data[item][0]['topic'],
            "id": grouped_data[item][0]['topic'],
            "sudden": len(grouped_data[item]) + 1
        })
    return res

## 重设参数
def set_model_param(data, id):
    model.config.epochs = data['epochs']
    model.config.dropout = data['dropout']
    model.config.learning_rate = data['learning_rate']
    model.config.regularizers_coeffiicient = data['regularize']
    model.config.atn_regularizers_coeffiicient = data['atn_regularize']
    AL.x_train = np.array([])
    AL.y_train = np.array([])
    ## 加载之前的训练数据
    lowerId = db.find_lower_loop(AL.data_pool.data_name, id)
    for item in lowerId:
        datas = db.find_loop_train_data(AL.data_pool.data_name, item)
        x, y = process_to_train(datas)
        if AL.x_train.shape[0] == 0:
            AL.x_train = x
            AL.y_train = y
            continue
        AL.x_train = np.concatenate((AL.x_train, x), axis=0)
        AL.y_train = np.concatenate((AL.y_train, y), axis=0)
    ## 开始训练
    uperLoops = db.find_loopData_upID(AL.data_pool.data_name, id)
    for item in uperLoops:
        recorder.train_status = []
        datas = db.find_loop_train_data(AL.data_pool.data_name, item)
        x, y, x_ver, y_ver = process_to_train(datas, return_ver=True)
        if AL.x_train.shape[0] == 0:
            AL.x_train = x
            AL.y_train = y
            continue
        AL.x_train = np.concatenate((AL.x_train, x), axis=0)
        AL.y_train = np.concatenate((AL.y_train, y), axis=0)
        recorder.training = True
        cbk = AtnCallback(score_name='f1')
        model.fit(AL.x_train, AL.y_train,
                  batch_size=model.config.batch_size,
                  epochs=model.config.epochs,
                  callbacks=cbk,
                  validation_data=(x_ver, y_ver),
                  shuffle=False
                  )
        recorder.update_train_record(item, AL.data_pool.data_name)
    recorder.training = False


## 加载训练数据
def process_to_train(db_data, return_ver=False):
    sequence = []
    labels = []
    w_seq = []
    w_label = []
    for sen, label in db_data:
        sen = json.loads(sen)
        sen = "".join(sen)
        sequence.append(sen)
        w_sen = list(sen)
        label = json.loads(label)
        if len(w_sen) == len(label):
            w_seq += w_sen
            w_label += label
            w_seq.append("#")
            w_label.append("#")
        labels.append(label)
    # pd = pandas.DataFrame({'word': w_seq, 'label': w_label})
    # pd.to_csv('./train_test.txt', header=None, sep=' ', index=None)
    if return_ver:
        x, y, x_ver, y_ver = model.data_man.get_train_data(slice=False,
                                                           from_file=False,
                                                           sequences=sequence,
                                                           labels=labels,
                                                           return_verify=return_ver,
                                                           verify_rate=0.5)
        return x, y, x_ver, y_ver
    else:
        x, y = model.data_man.get_train_data(slice=False,
                                             from_file=False,
                                             sequences=sequence,
                                             labels=labels,
                                             return_verify=return_ver,
                                             verify_rate=0.5)
        return x, y


def re_label(loop):
    data = db.find_loop_data(AL.data_pool.data_name, loop)
    ids = [item[0] for item in data]
    db.update_status(AL.data_pool.data_name, ids, status=1)
    AL.data_pool.selected_idx = ids

def look_loop(loop):
    data = db.find_loop_data(AL.data_pool.data_name, loop)
    ids = [item[0] for item in data]
    AL.data_pool.selected_idx = ids
    AL.loop = loop
    AL.predict = False
    sample_entities, data_list, loop = select_samples()
    return sample_entities, data_list, loop

def get_data_info():
    return [AL.data_pool.data_name, AL.data_pool.score_name, AL.data_pool.selected_idx]


def predict_by_text(text):
    label, entity = model.predict_user([text])
    return label[0], entity[0]


def predict_unlabeled():
    AL.predict_unlabeled()
