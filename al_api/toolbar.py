import json
import os.path
import re
import pandas
import requests
import zhconv
from untils import DataBase as db
from untils.PathManger import get_root_path

def load_source_data(data, filename):
    # try:
    for item in data:
        item['content'] = [remove_parentheses(zhconv.convert(sen, 'zh-hans')) for sen in item['content']]
        item['title'] = zhconv.convert(item['title'], 'zh-hans')
        item['author'] = zhconv.convert(item['author'], 'zh-hans')
    db.create_data_table(filename)
    db.insert_data2table(data, filename)
    return 1
    # except:
    #     return 0

def remove_parentheses(text):
    pattern = r'\([^()]*\)'  # 匹配括号及其内容
    cleaned_text = re.sub(pattern, '', text)  # 替换括号及其内容为空字符串
    return cleaned_text


def get_data_name():
    try:
        names = db.get_tables_name()
        return names
    except:
        return 0

def remove_data(name):
    try:
        db.delete_table(name)
        return 1
    except:
        return 0


from itertools import groupby
def get_train():
    conn, cur = db.open_db('source')
    cur.execute("select content, label, loop from poet where status==2")
    res = [row for row in cur.fetchall()]
    for i in range(15):
        loop_data = [item for item in res if item[2] == i]
        contents = []
        labels = []
        for conten, label, loop in loop_data:
            conten = json.loads(conten)
            label = json.loads(label)
            conten = "".join(conten)
            conten = list(conten)
            if len(label) != len(conten):
                continue
            conten.append("#")
            label.append('#')
            contents += conten
            labels += label
        data = pandas.DataFrame({"content":contents, "label": labels})
        data.to_csv(f'./{i}.txt', header=None, index=None, encoding='utf8', sep=' ')


# def time_record(time):
#     root = get_root_path()
#     with open(os.path.join(root, "data/time_MNLP.txt"), 'a+', encoding='utf8') as fp:
#         fp.write(time+'\n')
#     fp.close()


def get_poem_list():
    data_list = db.find_data_list('alltangs')
    re_data = []
    for item in data_list:
        ens = json.loads(item[6])
        if len(ens) > 0:
            re_data.append({'id': item[0], 'title': item[1], 'labeled': item[10]})
    return re_data


def get_train_file():
    conn, cur = db.open_db('source')
    cur.execute("select content, label from tangs where status>0")
    res = [row for row in cur.fetchall()]
    contents = []
    labels = []
    for conten, label in res:
        conten = json.loads(conten)
        label = json.loads(label)
        conten = "".join(conten)
        conten = list(conten)
        if len(label) != len(conten):
            continue
        conten.append("#")
        label.append('#')
        contents += conten
        labels += label
    data = pandas.DataFrame({"content": contents, "label": labels})
    data.to_csv(f'./train_radom.txt', header=None, index=None, encoding='utf8', sep=' ')


def get_entity_num(entity):
    return db.get_entity_num(entity)