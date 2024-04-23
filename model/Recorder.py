# @time:2023/5/3 13:42
# @functional:
from untils import DataBase as db
import json

## 记录数据的类
class Recorder:
    def __init__(self):
        self.USE_AC = True
        self.train_status = {}
        self.training = False
        self.operating_record = []
        self.data_name = 'zhs_0001'
        self.score_name = 'LC'

    def get_train_status(self):
        return self.train_status

    def set_train_status(self, data):
        self.train_status = data

    def add_train_record(self, epoch, data_name, samples):
        if self.training:
            return
        if self.training and len(self.train_status) == 0:
            return
        else:
            db.insert_record([epoch, self.train_status, samples, data_name])
            self.train_status = {}

    def update_train_record(self, epoch, data_name):
        db.update_record(epoch, data_name, self.train_status)
        self.train_status = {}

    def add_operation(self, loop, data):
        for item in self.operating_record:
            if item['name'] == f'loop{loop}':
                if 'data' not in item.keys():
                    item['data'] = []
                item['data'].append(data)
                break
        else:
            self.operating_record.append({'name': f'loop{loop}', 'data': [data], 'operation': []})

    def init_operation_record(self):
        loops = db.query_grouped_loop(self.data_name)
        for loop in loops:
            samplesID = db.query_grouped_sample(loop, self.data_name)
            data = []
            for sample in samplesID:
                samp_info = db.find_data_list_by_id(self.data_name, [sample])[0]
                # size = db.count_sample_record(sample)
                data.append({'id': sample, 'name': samp_info[1], 'value': samp_info[2] if self.score_name == 'LC'
            else samp_info[3]})
            self.operating_record.append({'name':f'loop{loop}', 'data': data})

    def set_data_info(self, data_name, score_name):
        self.data_name = data_name
        self.score_name = score_name
        self.init_operation_record()


    #***************************************接口api*************************************
    def get_train_record(self, data_name):
        res = db.get_all_record(data_name)
        record = []
        for epoch, train_log, ids, name, vallog in res:
            # 折线图数据
            train_log = json.loads(train_log)
            vallog = json.loads(vallog)
            ids = json.loads(ids)
            record.append({
                'x': epoch,
                'y': vallog[1],
                'loss': train_log['loss'],
                'epoch_val_f1': train_log['val_f1'],
                'ids': ids
            })
        return record



recorder = Recorder()
