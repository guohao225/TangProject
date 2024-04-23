import json
import os
os.environ['TF_KERAS'] = '1'
import tensorflow as tf
gpu_devices = tf.config.experimental.list_physical_devices('GPU')
for device in gpu_devices: tf.config.experimental.set_memory_growth(device, True)
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS, cross_origin
from al_api import toolbar
# from al_api import toolbar, query
from model.Recorder import recorder
from activteLearner import ActiveLearning

ACTIVE_AL = True
Review = False
tf.random.set_seed(42)
os.environ["PYTHONHASHSEED"] = str(42)

# 全局跨域
app = Flask(__name__)
CORS(app, supports_credentials=True)

## 初始化al,初始化时更新选择分数
al = ActiveLearning(50, 'alltangs')
al.update_score()
## 初始化学习器
# active_learing.init_al()

@app.route('/load_source_data', methods=['POST'])
def load_source_data():
    data = request.get_json()['json']
    name = request.get_json()['filename']
    res = toolbar.load_source_data(data, name)
    return {
        'res': res
    }

@app.route('/remove_data', methods=['POST'])
def remove_data():
    name = request.get_json()['name']
    res = toolbar.remove_data(name)
    return jsonify(res=res)

@app.route('/get_all_data', methods=['GET'])
def get_all_data():
    names = toolbar.get_data_name()
    return jsonify(res=names)


@app.route('/init', methods=['POST'])
def init():
    global ACTIVE_AL
    data = request.get_json()['data']
    if data['strategy'] == 'None':
        ACTIVE_AL = False
    if ACTIVE_AL:
        print(al.loop)
        if not Review:
            al.update_parameter(data)
        sample, idx, loop = al.get_selected_data()
    return jsonify(res=sample, list=idx, loop=loop)

@app.route('/one_loop_tag', methods=['GET'])
def one_loop_tag():
    if ACTIVE_AL:
        ## 训练标注的数据
        al.extract_loop_entities()
        al.epoch_tag_down()
        al.update_score()
        al.select_samples()
        ## 获取新的需要标注的数据
        sample, idx, loop = al.get_selected_data()
    else:
        pass
    return jsonify(res=sample, list=idx, loop=loop)

@app.route('/look_loop', methods=['POST'])
def look_loop():
    global Review
    loop = request.get_json()['loop']
    sample_entities, data_list, loop = al.look_loop(loop)
    Review = True
    return jsonify(res=sample_entities, list=data_list, loop=loop)

## 查询是否处于训练状态
@app.route('/train_status', methods=['GET'])
def train_status():
    status = recorder.training
    status = 1 if status else 0
    return jsonify(res=status)

## 查询训练历史数据
@app.route('/get_train_record', methods=['GET'])
def get_train_record():
    data = recorder.get_train_record(al.data_pool.data_name)
    return jsonify(res=data)

#
@app.route('/get_selected_data', methods=['GET'])
def get_selected_data():
    sample, idx, loop = al.get_selected_data()
    suggest = al.find_suggest()
    return jsonify(res=sample, list=idx, loop=loop, suggest=suggest)

# @app.route('/get_selected_data_by_id', methods=['POST'])
# def get_selected_data_by_id():
#     id = request.get_json()['id']
#     sample, idx, loop = al.get_selected_data_by_id(id)
#     return jsonify(res=sample, list=idx, loop=loop)
#
@app.route('/get_suggest', methods=['get'])
def get_suggest():
    res = al.find_suggested()
    return jsonify(res=res)
#
@app.route('/get_tag_sample', methods=['POST'])
def get_tag_sample():
    id = request.get_json()['id']
    res = al.get_tag_sample(id)
    return jsonify(res=res)


@app.route('/tag_update', methods=['POST'])
def tag_update():
    data = request.get_json()['data']
    if Review:
        res = al.tag_update(data, 2)
    else:
        res = al.tag_update(data, 1)
    return jsonify(res=res)


@app.route('/get_format_label', methods=['POST'])
def get_format_label():
    data = request.get_json()['data']
    res = al.get_format_label(data)
    return jsonify(res=res)

@app.route('/tag_update_batch', methods=['POST'])
def update_many():
    data = request.get_json()['data']
    print(data)
    res = al.update_many_label(data)
    return jsonify(res=res)


@app.route('/insert_time', methods=['POST'])
def insert_time():
    time = request.get_json()['time']
    res = al.time_record(time)
    return jsonify(res=res)

#

#

#
# @app.route('/insert_oper_record', methods=['POST'])
# def insert_oper_record():
#     data = request.get_json()['data']
#     res = record.insert_oper_record(data)
#     return jsonify(res=res)
#
# @app.route('/get_oper_record', methods=['GET'])
# def get_oper_record():
#     return jsonify(res = recorder.operating_record)
#
# @app.route('/query_record_sample', methods=['POST'])
# def query_record_sample():
#     id = request.get_json()['id']
#     loop = request.get_json()['loop']
#     res = record.query_record_sample(id, loop)
#     return jsonify(res = res)
#
# @app.route('/query_record_loop', methods=['POST'])
# def query_record_loop():
#     loop = request.get_json()['loop']
#     res = record.query_record_loop(loop)
#     return jsonify(res = res)
#
# from al_api import active_learing
@app.route('/sample_statistics', methods=['GET'])
def sample_statistics():
    res = al.find_all_samples()
    return jsonify(res=res)
#
# @app.route('/operate_sample',methods=['POST'])
# def operate_sample():
#     id = request.get_json()['id']
#     type = request.get_json()['type']
#     if type == 0:
#         active_learing.AL.data_pool.add_selected(id)
#     if type == 1:
#         active_learing.AL.data_pool.remove_selected(id)
#     else:
#         active_learing.AL.data_pool.remove_labeled(id)
#     return jsonify(res=1)
#
#
@app.route('/get_all_loop_entitys', methods=['POST'])
def get_all_loop_entitys():
    res = al.get_loop_entity()
    return jsonify(res=res)

@app.route('/get_all_entitys', methods=['GET'])
def get_all_entitys():
    res = al.get_all_entities()
    return jsonify(res=res)

@app.route('/get_loop_labeledandunlabel', methods=['GET'])
def get_loop_labeledandunlabel():
    res = al.get_loop_labeledandunlabel()
    return jsonify(res=res)

@app.route('/get_all_labeledandunlabel', methods=['GET'])
def get_all_labeledandunlabel():
    res = al.get_all_labeledandunlabel()
    return jsonify(res=res)

@app.route('/get_all_PERANDLOCANDTIME', methods=['GET'])
def get_all_PERANDLOCANDTIME():
    res = al.get_all_PERANDLOCANDTIME()
    return jsonify(res=res)

@app.route('/get_all_time_record', methods=['GET'])
def get_all_time_record():
    res = al.get_label_time()
    return jsonify(res=res)

@app.route('/query_select_status', methods=['GET'])
def query_select_status():
    if len(al.data_pool.selected_idx) > 0:
        return jsonify(res=1)
    else:
        return jsonify(res=0)

@app.route('/relation_types', methods=['GET'])
def get_relation_types():
    with open('./data/relations.json', 'r', encoding='utf8') as f:
        data = json.load(f)
    f.close()
    return jsonify(res=data)

@app.route('/update_relations', methods=['POST'])
def update_relations_types():
    data = request.get_json()['data']
    with open('./data/relations.json', 'w', encoding='utf8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    return jsonify(res=data)

@app.route('/query_entity_num', methods=['POST'])
def query_entity_num():
    data = request.get_json()['entity']
    res = toolbar.get_entity_num(data)
    return jsonify(num=res)



if __name__ == '__main__':
    # al.get_loop_entity()
    app.run(debug=False)
#
# @app.route('/fine_tuning_model', methods=['POST'])
# def fine_tuning_model():
#     data = request.get_json()['data']
#     id = request.get_json()['id']
#     active_learing.set_model_param(data, id)
#     return jsonify(res=1)
#
#
# @app.route('/re_label', methods=['POST'])
# def re_label():
#     loop = request.get_json()['loop']
#     active_learing.re_label(loop)
#     return jsonify(res=1)
#
# @app.route('/query_dic_text', methods=['POST'])
# def query_dic_text():
#     text = request.get_json()['text']
#     label, entity = query.query_entity_by_dic(text, active_learing.config.max_sequence_len)
#     return jsonify(label=label, entity=entity)
#
#
# @app.route('/query_text_model', methods=['POST'])
# def query_text_model():
#     text = request.get_json()['text']
#     label, entity = active_learing.predict_by_text(text)
#     return jsonify(label=label, entity=entity)
#
#
# @app.route('/query_word', methods=['GET', 'POST'])
# def query_word():
#     word = request.get_json()['word']
#     if word == {}:
#         return
#     content = query.word_query(word)
#     return jsonify(res=str(content))
#
#
# @app.route('/query_note', methods=['POST'])
# def query_note():
#     text = request.get_json()['text']
#     note = query.query_poem_tip(text)
#     return jsonify(res=note)
#

#
# @app.route('/look_loop', methods=['POST'])
# def look_loop():
#     loop = request.get_json()['loop']
#     config = request.get_json()['config']
#     active_learing.set_config(config)
#     sample_entities, data_list, loop = active_learing.look_loop(loop)
#     return jsonify(res=sample_entities, list=data_list, loop=loop)

# @app.route('/add_time', methods=['POST'])
# def add_time():
#     time = request.get_json()['time']
#     toolbar.time_record(time)
#     return jsonify(res=1)
#
# @app.route('/get_poem_list', methods=['GET'])
# def get_poem_list():
#     return jsonify(res=toolbar.get_poem_list())


