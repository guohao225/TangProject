import json
import os
import numpy as np
from untils.DataManger import data_manger
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.losses import SparseCategoricalCrossentropy
from untils.Config import CONFIG
from model.NerModel import NerModel, NERMetrics, AtnCallback
import untils.DataBase as db
import tensorflow as tf
from untils import evaluate as eva
from model.Recorder import recorder
import random


class DataPool(object):
    unlabel_pool = []
    labeled_pool = []
    selected_idx = []
    d_name = ""
    s_name = ''

    def __init__(self, data_name, num_samples, score_name='LC'):
        self.data_name = data_name
        self.num_sample = num_samples
        self.score_name = score_name
        self.unlabel_pool = db.find_label_data(data_name, 0)
        self.labeled_pool = db.find_label_data(data_name, 1)

    def get_labeled_data(self):
        self.labeled_pool = db.find_label_data(self.data_name, 1)
        return self.labeled_pool

    def get_unlabeled_data(self):
        self.unlabel_pool = db.find_unlabel(self.data_name)
        return self.unlabel_pool

    def remove_selected(self, id):
        if id in self.selected_idx:
            self.selected_idx.remove(id)
        db.update_select(self.data_name, [id], 0)

    def add_selected(self, id):
        if id not in self.selected_idx:
            self.selected_idx.append(id)
        db.update_select(self.data_name, [id], 1)

    def remove_labeled(self, id):
        db.update_status(self.data_name, [id], 0)

    def get_selected_idx(self):
        try:
            idx = db.find_score(self.data_name, self.score_name, self.num_sample)
            self.selected_idx = idx
            return idx
        except:
            return []

    @classmethod
    def getMsg(cls):
        data = [DataPool.d_name, DataPool.s_name]
        return data

    def update_LC(self, ids, lcs):
        db.update_data_number(self.data_name, ids, 'LC', lcs)

    def update_MNLP(self, ids, mnlps):
        db.update_data_number(self.data_name, ids, 'MNLP', mnlps)

    def update_tag_scores(self, ids, tag_scores):
        tag_scores = [score.numpy().tolist() for score in tag_scores]
        db.update_data_obj(self.data_name, ids, 'label_score', tag_scores)

    def update_label(self, ids, labels):
        db.update_data_obj(self.data_name, ids, 'label', labels)

    def update_entity(self, ids, entitys):
        db.update_data_obj(self.data_name, ids, 'entitys', entitys)


class ActiveLearning:
    def __init__(self, select_num, data_name, score_name='LC'):
        self.data_pool = DataPool(data_name, select_num, score_name)
        self.model = NerModel()
        self.loop = 0
        self.predict = True
        self.x_train = np.array([])
        self.y_train = np.array([])
        self.train_record = {}
        self.init()

    def compute_uncertainty(self, sequence):
        LCS = []
        MNLPS = []
        ## 计算最小置信度
        for item in sequence:
            ## 替换小于0.5的值，替换为1-该值
            item = tf.where(item < 0.5, 1 - item, item)
            ##计算LC
            ## 计算最后一维维所有元素的乘积
            temp = tf.reduce_prod(item, axis=-1)
            LC = tf.reduce_sum(temp)
            ## 计算MNLP
            log_item = tf.math.log(item)
            mnlp_temp = tf.reduce_sum(log_item, axis=-1)
            MNLP = tf.reduce_sum(mnlp_temp)
            MNLP_confidence = MNLP / (item.shape[0])
            LCS.append(LC.numpy())
            MNLPS.append(MNLP_confidence.numpy())
        return LCS, MNLPS

    def update_score(self): ## 每一轮更新选择策略的样本分数
        print("***************************开始更新分数************************")
        unlabel_data = self.data_pool.get_unlabeled_data()
        ids = [item[0] for item in unlabel_data]
        content = ["".join(json.loads(item[3])) for item in unlabel_data]
        ## 将数据处理为模型需求的格式
        sequence, mask, lens, segs = data_manger.bert_embedding_sentences(content)
        ## 预测数据
        if len(sequence) == 0:
            return []
        sequence = data_manger.concat_inputs(sequence, mask, segs)
        decoded_sequence, logist, sequence_length, _ = self.model.predict(sequence)
        print("***************************更新完成********************************")
        print("***************************开始计算LC和MNLP********************************")
        ## 计算最大分数
        tag_scores = eva.get_tag_score(logist)
        ## 计算不确定性
        # 获取真实的句子预测序列
        logist = eva.get_real_logist(logist, lens)
        tag_scores = eva.get_real_logist(tag_scores, lens)
        if self.data_pool.score_name != "Random":
            lcs, mnlps = self.compute_uncertainty(logist)
        else:
            lcs = [100 + random.random() * 50 for index in ids]
            mnlps = [random.random() for index in ids]
        print("***************************计算完成********************************")
        ## 更新数据库
        self.data_pool.update_LC(ids, lcs)
        self.data_pool.update_MNLP(ids, mnlps)
        seq = NerModel.get_tag_seq(logist)
        seq_entitys = NerModel.extract_entities(seq, tag_scores, content)
        self.data_pool.update_entity(ids, seq_entitys)
        self.data_pool.update_label(ids, seq)
        self.data_pool.update_tag_scores(ids, tag_scores)

    def select_samples(self):
        ##获取当前轮次选择的样本id
        self.data_pool.get_selected_idx()
        ##更新数据库状态
        db.update_select(self.data_pool.data_name, self.data_pool.selected_idx, 1)
        return self.data_pool.selected_idx

    def epoch_tag_down(self):
        ## 获取该伦次之前的标注数据
        train_data = db.find_lower_loop_data(self.data_pool.data_name, self.loop)
        x, y = self.process_to_train(train_data)
        self.x_train = x
        self.y_train = y
        # 获取标注的数据
        idx = self.data_pool.selected_idx
        # 将标注的数据处理为训练数据
        train_data = db.find_train_data(self.data_pool.data_name, idx)
        sequence = []
        labels = []
        for sen, label in train_data:
            sen = json.loads(sen)
            sen = "".join(sen)
            sequence.append(sen)
            label = json.loads(label)
            labels.append(label)
        x, y, mask, seq_len, segs = data_manger.bert_embedding_sequence(sequence, labels, shuffle=False)
        x = data_manger.concat_inputs(x, mask, segs)
        if self.x_train.shape[0] == 0 or self.y_train.shape[0] == 0:
            self.x_train = x
            self.y_train = y
        else:
            self.x_train = np.concatenate((self.x_train, x), axis=0)
            self.y_train = np.concatenate((self.y_train, y), axis=0)
        # 打乱样本
        samples = len(self.x_train)
        index = np.arange(samples)
        np.random.shuffle(index)
        self.x_train = self.x_train[index]
        self.y_train = self.y_train[index]
        self.x_train = self.x_train[0:int(len(self.x_train)*0.8)]
        self.y_train = self.y_train[0:int(len(self.y_train)*0.8)]
        x_dev = self.x_train[int(len(self.x_train)*0.8):-1]
        y_dev = self.y_train[int(len(self.y_train)*0.8):-1]
        # 训练数据
        self.reset_model()
        print("************************training begin*****************************")
        recorder.training = True
        cbk = AtnCallback()
        train_his = self.model.fit(self.x_train, self.y_train, validation_data=(x_dev, y_dev), batch_size=30, epochs=20, callbacks=cbk)
        # self.model = self.load_weights(os.path.join(CONFIG.root_path, f'checkpoints/{CONFIG.save_path}'))
        his = self.model.evaluate(x_dev, y_dev)
        recorder.set_train_status({"trainlog": train_his.history, "vallog": his})
        recorder.training = False
        print("************************training end!!!*****************************")

        # 添加一条训练记录
        recorder.add_train_record(self.loop, self.data_pool.data_name, idx)
        # # 更新数据库中标注的状态
        db.update_status(self.data_pool.data_name, idx, 2)
        db.update_select(self.data_pool.data_name,self.data_pool.selected_idx, 0)
        # # 更新轮次信息
        db.update_loop(self.data_pool.data_name, idx, self.loop)
        # # 将标注的数据加入到已标注的数组中
        # self.data_pool.labeled_pool += self.data_pool.selected_idx
        # 清空样本选择数组
        self.data_pool.selected_idx = []
        self.loop += 1

    def get_ver(self):
        path = os.path.join(self.model.config.root_path, 'data/dev.txt')
        x, y, mask = self.model.data_man.bert_embedding_from_file(path)
        samples = len(x)
        index = np.arange(samples)
        np.random.shuffle(index)
        # 打乱样本
        x = x[index]
        y = y[index]
        x_dev = x[0:int(len(x) * 0.9)]
        y_dev = y[0:int(len(y) * 0.9)]
        x_ver = x[int(len(x) * 0.9):-1]
        y_ver = y[int(len(x) * 0.9):-1]
        return x_ver, y_ver, x_dev, y_dev

    def reset_model(self):
        self.model = NerModel()
        self.model.compile(optimizer=Adam(learning_rate=CONFIG.learning_rate),
                           loss=SparseCategoricalCrossentropy(),
                           metrics=[NERMetrics(name='f1')])

    def extract_loop_entities(self):
        sample_entities, data_list, self.loop = self.get_selected_data()
        # sample_entities对象数组根据name分类
        classified_entities = {}
        for item in sample_entities:
            if item['type'] != 'sample':
                name = item['name']+','+item['type']
                if name in classified_entities:
                    classified_entities[name].append({'name': item['name'], 'id': item['id'], 'type': item['type']})
                else:
                    classified_entities[name] = [{'name': item['name'], 'id':item['id'], 'type': item['type']}]

        # 分类后对象处理为数据库需求的格式
        process_data = []
        for key in classified_entities:
            process_data.append([key, key.split(',')[0], [e['id'] for e in classified_entities[key]], len(classified_entities[key]),
                                 classified_entities[key][0]['type']])
        db.insert_entity(process_data, self.loop)


    def predict_unlabeled(self):
        unlabel_data = self.data_pool.get_unlabeled_data()
        ids = [item[0] for item in unlabel_data]
        content = ["".join(json.loads(item[3])) for item in unlabel_data]
        ## 将数据处理为模型需求的格式
        sequence, mask, lens, segs = data_manger.bert_embedding_sentences(content)
        sequence = data_manger.concat_inputs(sequence, mask, segs)

        ## 预测数据
        if len(sequence) == 0:
            return []
        decoded_sequence, logist, sequence_length, _ = self.model.predict(sequence)
        tag_scores = eva.get_tag_score(logist)
        ## 计算不确定性
        # 获取真实的句子预测序列
        logist = eva.get_real_logist(logist, lens)
        tag_scores = eva.get_real_logist(tag_scores, lens)

        ## 更新数据库
        seq = NerModel.get_tag_seq(logist)
        seq_entitys = NerModel.extract_entities(seq, tag_scores)
        self.data_pool.update_entity(ids, seq_entitys)
        self.data_pool.update_label(ids, seq)
        self.data_pool.update_tag_scores(ids, tag_scores)

    def init(self):
        # db.reset_loop(self.data_pool.data_name)
        # db.reset_status(self.data_pool.data_name)
        # db.reset_train_record()
        self.loop = db.find_max_loop(self.data_pool.data_name) + 1
        self.model.compile(optimizer=Adam(learning_rate=CONFIG.learning_rate),
                           loss=SparseCategoricalCrossentropy(),
                           metrics=[NERMetrics(name='f1')])
        self.model.load_weights(os.path.join(CONFIG.root_path, f'checkpoints/{CONFIG.save_path}'))
        # db.reset_entities_record()
        # db.reset_time_record()
        # train_data = db.find_labeled_data(self.data_pool.data_name)
        # x, y = self.process_to_train(train_data)
        # self.x_train = x
        # self.y_train = y

    def process_to_train(self, db_data):
        sequence = []
        labels = []
        for sen, label in db_data:
            sen = json.loads(sen)
            sen = "".join(sen)
            sequence.append(sen)
            label = json.loads(label)
            labels.append(label)
        if len(sequence) > 0:
            x, y, mask, sens, segs = data_manger.bert_embedding_sequence(sequence, labels)
            x = data_manger.concat_inputs(x, mask, segs)
            return x, y
        else:
            return np.array([]), np.array([])

    def get_sample_list(self, ids):
        res = db.find_data_list_by_id(self.data_pool.data_name, ids)
        data_list = []
        for item in res:
            data_list.append({'id': item[0], 'title': item[1], 'LC': item[2], 'MNLP': item[3], 'ENTITY_MNLP': item[4], "status":item[5]})
        return data_list

    ## *************************************************************************************************##
    ## ******************************************API接口*************************************************##
    ## *************************************************************************************************##
    def update_parameter(self, data):
        select_num = data['select_num']
        data_name = data['data_name']
        strategy = data['strategy']

        ###更新datapool
        self.data_pool.data_name = data_name
        self.data_pool.num_sample = select_num
        self.data_pool.score_name = strategy

        ## 更新select_idx
        self.data_pool.get_selected_idx()

    def tag_update(self, data, status):
        id = data['id']
        label = data['label']
        relations = data['relations']
        print(relations)
        # 查找当前记录的标注数据
        sample_data = db.find_data_by_id(self.data_pool.data_name, [id])[0]
        old_label = json.loads(sample_data[4])
        old_entity = json.loads(sample_data[6])
        content = "".join(json.loads(sample_data[3]))
        entitys = eva.extract_entities(label, content, tf.convert_to_tensor([1 for x in range(len(label))]))

        db.update_data_number(self.data_pool.data_name, [id], 'status', [status])
        db.update_data_obj(self.data_pool.data_name, [id], 'label', [label])
        db.update_data_obj(self.data_pool.data_name, [id], 'entitys', [entitys])
        db.update_data_obj(self.data_pool.data_name, [id], 'user_label', [label])
        db.update_data_obj(self.data_pool.data_name, [id], 'user_entitys', [old_entity])
        db.update_data_obj(self.data_pool.data_name, [id], 'relations', [relations])
        # 添加操作记录
        return 1

    def update_many_label(self, data):
        # data = {name...:, type:.., oper}
        db.update_many_label(self.data_pool.data_name, data, self.data_pool.selected_idx)
        return 1


    def get_selected_data(self):
        data_list = self.get_sample_list(self.data_pool.selected_idx)
        ##查询样本的具体信息
        samples = db.find_data_by_id(self.data_pool.data_name, self.data_pool.selected_idx)
        ### 解析实体信息
        sample_entities = []
        for item in samples:
            entities = json.loads(item[6])
            if len(entities) > 0:
                entities = [{'id': item[0],
                             'name': ent[1],
                             'score': ent[4],
                             'type': ent[0],
                             'LC': item[7],
                             'MNLP': item[8],
                             'entity_MNLP': item[9],
                             'status': item[10],
                             'size':db.get_weight_by_name(f'{ent[1]},{ent[0]}')
                             # 'size':5
                             # 'size': db.find_frequency(content[ent[1]:ent[2] + 1], self.data_pool.data_name)
                             } for ent in entities if len(ent) == 5]
            else:
                entities = [{'id': item[0],
                             'name': item[1],
                             'score': 0.5,
                             'type': 'sample',
                             'LC': item[7],
                             'MNLP': item[8],
                             'entity_MNLP': item[9],
                             'status': item[10],
                             'size': 10
                             }]
            sample_entities += entities
        return sample_entities, data_list, self.loop

    def find_all_samples(self):
        all_samples = db.find_data_list(self.data_pool.data_name)
        PER = []
        LOC = []
        TIME = []
        res = []
        for item in all_samples:
            tem = {'name': item[1], 'clarity': "", 'score': item[7 if self.data_pool.score_name == 'LC' else 8],
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

    def find_suggest(self):
        res = db.find_suggest(self.data_pool.data_name, self.data_pool.selected_idx, self.data_pool.score_name)
        return res

    def get_loop_entity(self):
        # data:[('寿丘,LOC', '[0, "14,767"]', '[0, 2]', 'LOC', '寿丘'), ('单于,PER', '[0, "14,767"]', '[0, 2]', 'PER', '单于')]
        data = db.query_all_entities()
        loopdict = {}
        result = []
        ## 计算每一个实体在每一轮的权重
        for item in data:
            weight_obj = item[2].split(';')
            ids_obj = item[1].split(';')
            weight_obj = [eval(e) for e in weight_obj]
            for e, ids in zip(weight_obj, ids_obj):
                if e[0] not in loopdict.keys():
                    loopdict[e[0]] = []
                weight = sum([w[1] for w in weight_obj if w[0] <= e[0]])
                loopdict[e[0]].append({"text": item[4],
                                       "topic": item[3],
                                       "frequency": weight,
                                       'id': str(e[0])+item[4],
                                       "ids": ids[1],
                                       "sudden": weight+1
                                       })
        for key in loopdict.keys():
            temp = {'date': key, 'words': {'person': [], 'location': [], 'time': []}}
            for item in loopdict[key]:
                if item['topic'] == 'PER':
                    item['topic'] = "person"
                    temp['words']['person'].append(item)
                if item['topic'] == 'LOC':
                    item['topic'] = "location"
                    temp['words']['location'].append(item)
                if item['topic'] == 'ORG':
                    item['topic'] = "time"
                    temp['words']['time'].append(item)
            result.append(temp)
        return result

    def get_all_entities(self):
        data = db.query_all_entities()
        res = []
        for item in data:
            weight_obj = item[2].split(';')
            weight_obj = [eval(e) for e in weight_obj]
            weight = 0
            for e in weight_obj:
                weight += e[1]
            res.append({'text': item[4], 'frequency': weight, 'topic': item[3]})
        return res

    def find_suggested(self):
        try:
            res = db.find_suggest(self.data_pool.data_name, self.data_pool.selected_idx, self.data_pool.score_name)
            return res
        except:
            return -1

    def get_tag_sample(self, id):
        try:
            res = db.find_data_by_id(self.data_pool.data_name, [id])[0]
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

    def get_label_time(self):
        record = db.get_all_time(self.data_pool.data_name)
        result = [{'name':item[0], "value":item[1]} for item in record]
        return result

    def get_loop_labeledandunlabel(self):
        labeled = db.get_labeledorunlabel(self.data_pool.data_name, self.data_pool.selected_idx, 1)
        unlabel = db.get_labeledorunlabel(self.data_pool.data_name, self.data_pool.selected_idx, 0)
        return [{'name':'labeled', "value":labeled}, {'name':'unlabel', "value":unlabel}]

    def get_all_labeledandunlabel(self):
        labeled = db.get_all_labeledorunlabel(self.data_pool.data_name, 2)
        unlabel = db.get_all_labeledorunlabel(self.data_pool.data_name, 0)
        return [{'name':'labeled', "value":labeled}, {'name':'unlabel', "value":unlabel}]

    def get_all_PERANDLOCANDTIME(self):
        per = len(db.query_entities_by_type('PER'))
        loc = len(db.query_entities_by_type('LOC'))
        time = len(db.query_entities_by_type('ORG'))
        return [{'name':'PER', "value":per}, {'name':'LOC', "value":loc}, {'name':'TIME', "value":time}]

    def get_format_label(self, data):
        label = data['label']
        id = data['id']
        sample_data = db.find_data_by_id(self.data_pool.data_name, [id])[0]
        content = "".join(json.loads(sample_data[3]))
        entitys = eva.extract_entities(label, content, tf.convert_to_tensor([1 for x in range(len(label))]))
        return entitys

    def time_record(self, time):
        db.insert_time_record(self.data_pool.data_name, self.loop, time)
        return 1

    def look_loop(self, loop):
        data = db.find_loop_data(self.data_pool.data_name, loop)
        ids = [item[0] for item in data]
        self.data_pool.selected_idx = ids
        self.loop = loop
        # self.select_samples()
        sample_entities, data_list, loop = self.get_selected_data()
        return sample_entities, data_list, loop










