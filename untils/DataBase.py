import json
import os.path
import sqlite3
from untils.PathManger import get_root_path


CHANGE_PATH = {"PER": "LOC", "LOC": "ORG", "ORG": "PER"}

# 数据库数据迁移
def open_db(db_name):
    root = get_root_path()
    conn = sqlite3.connect(os.path.join(root, f'data/{db_name}.db'))
    cur = conn.cursor()
    return conn, cur

def create_data_table(table_name):
    conn, cur = open_db('source')
    sql = f'''CREATE TABLE {table_name}(
            id integer primary key autoincrement,
            title text not null,
            author text not null,
            content text not null,
            label text,
            label_score text,
            entitys text,
            LC real,
            MNLP real,
            entity_MNLP real,
            status integer not null,
            user_label text,
            user_entitys text,
            loop integer default -1,
            selected integer default 0
    )
    '''
    cur.execute(sql)
    conn.commit()
    conn.close()

def create_entities_table():
    conn, cur = open_db('source')
    sql = f'''CREATE TABLE entities(
                name text primary key,
                real_name text not null,
                ids text not null,
                weight integer not null,
                type text not null,
                loop integer not null,
        )
        '''
    cur.execute(sql)
    conn.commit()
    conn.close()

def insert_data2table(data, table_name):
    conn, cur = open_db('source')
    for item in data:
        cur.execute(f"insert into {table_name} (title, author, content, status) values (?, ?, ?, ?)", (item['title'], item['author']
                    , json.dumps(item['content'], indent=2, ensure_ascii=False), 0))
    conn.commit()
    conn.close()

def get_tables_name():
    conn, cur = open_db('source')
    cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cur.fetchall()
    tables = [table_name[0] for table_name in tables]
    for i in range(3):
        del tables[0]
    return tables

def delete_table(table_name):
    conn, cur = open_db('source')
    cur.execute(f'DROP TABLE {table_name};')
    conn.commit()
    conn.close()

def reset_loop(table_name):
    conn, cur = open_db('source')
    cur.execute(f'update {table_name} set loop=-1')
    conn.commit()
    conn.close()

def reset_status(table_name):
    conn, cur = open_db('source')
    cur.execute(f'update {table_name} set status=0')
    conn.commit()
    conn.close()

def reset_train_record():
    conn, cur = open_db('source')
    cur.execute(f'delete from train_record')
    conn.commit()
    conn.close()

def find_label_data(table_name, status=0):
    conn, cur = open_db('source')
    cur.execute(f'select * from {table_name} where status=(?)',(status,))
    result = cur.fetchall()
    conn.close()
    return result

def find_labeled_data(table_name):
    conn, cur = open_db('source')
    res = cur.execute(f'select content, label from {table_name} where status>0')
    result = [row for row in res.fetchall()]
    conn.close()
    return result

def find_lower_loop_data(table_name, loop):
    conn, cur = open_db('source')
    res = cur.execute(f'select content, user_label from {table_name} where loop<{loop} and loop>=0')
    result = [row for row in res.fetchall()]
    conn.close()
    return result

def find_score(table_name, score_name, num_sample):
    conn, cur = open_db('source')
    if score_name == "Random":
        cur.execute(f'select id from {table_name} where status<2 and LC<200 and length(content)<200 order by RANDOM() limit {num_sample}')
    elif score_name == "MNLP":
        cur.execute(f'select id from {table_name} where status<2 and {score_name}<200 and length(content)<250 order by {score_name} limit {num_sample}')
    else:
        cur.execute(f'select id from {table_name} where status<2 and {score_name}<200 and length(content)<280 order by {score_name} DESC limit {num_sample}')
    result = [row[0] for row in cur.fetchall()]
    conn.close()
    return result

def find_score_by_sn(table_name, score_name, ids):
    conn, cur = open_db('source')
    if score_name == "Random":
        score_name = "LC"
    cur.execute(f'select title, {score_name} from {table_name} where id in ({",".join("?"*len(ids))})', ids)
    result = [row for row in cur.fetchall()]
    conn.close()
    return result

def update_data_number(table_name, ids, update_name, update_values):
    conn, cur = open_db('source')
    for i in range(len(ids)):
        cur.execute(f'update {table_name} set {update_name}=? where id=?', (float(update_values[i]), ids[i]))
    conn.commit()
    conn.close()

def update_data_obj(table_name, ids, update_name, update_values):
    conn, cur = open_db('source')
    for i in range(len(ids)):
        if update_name == 'label':
            cur.execute(f'update {table_name} set {update_name}=? where id=? and status=0',
                        (json.dumps(update_values[i], ensure_ascii=False), ids[i]))
        else:
            cur.execute(f'update {table_name} set {update_name}=? where id=?',
                        (json.dumps(update_values[i], ensure_ascii=False), ids[i]))
    conn.commit()
    cur.close()
    conn.close()

def find_data_by_id(table_name, ids):
    conn, cur = open_db('source')
    sql = f'select * from {table_name} where id in ({",".join("?"*len(ids))})'
    res = cur.execute(sql, ids)
    res = [row for row in res.fetchall()]
    cur.close()
    conn.close()
    return res

def find_max_loop(data_name):
    conn, cur = open_db('source')
    sql = f'select Max(loop) from {data_name}'
    cur.execute(sql)
    res = cur.fetchone()[0]
    cur.close()
    conn.close()
    return res

def find_data_list_by_id(table_name, ids):
    conn, cur = open_db('source')
    sql = f'select id,title,LC,MNLP,entity_MNLP,status from {table_name} where id in ({",".join("?" * len(ids))})'
    res = cur.execute(sql, ids)
    res = [row for row in res.fetchall()]
    return res

def find_data_list(table_name):
    conn, cur = open_db('source')
    sql = f'select * from {table_name} where length(content)<202'
    res = cur.execute(sql)
    res = [row for row in res.fetchall()]
    return res

def find_suggest(table_name, ids, score_name):
    conn, cur = open_db('source')
    sql = "SELECT id from {} WHERE id IN ({}) AND status = 0 ORDER BY {} DESC LIMIT 1"\
        .format(table_name,','.join(['?']*len(ids)), score_name)
    cur.execute(sql, ids)
    result = cur.fetchone()
    conn.close()
    return result[0]

def update_status(data_name, ids, status=2):
    conn, cur = open_db('source')
    sql = 'update {} set status={} where id in ({})'\
        .format(data_name, status, ",".join("?"*len(ids)))
    cur.execute(sql, ids)
    conn.commit()
    conn.close()

def update_select(data_name, ids, select_status = 1):
    conn, cur = open_db('source')
    cur.execute(f'update {data_name} set selected=0')
    sql = 'update {} set selected={} where id in ({})' \
        .format(data_name, select_status, ",".join("?" * len(ids)))
    cur.execute(sql, ids)
    conn.commit()
    conn.close()

def update_loop(data_name, ids, loop):
    conn, cur = open_db('source')
    sql = 'update {} set loop={} where id in ({})' \
        .format(data_name, loop, ",".join("?" * len(ids)))
    cur.execute(sql, ids)
    conn.commit()
    conn.close()


def update_many_label(data_name, data, ids):
    conn, cur = open_db('source')
    sql = "select id, label, entitys from {} where entitys like '%{}%' and id in ({})" \
        .format(data_name, '"'+data['type']+'"'+", "+'"'+data['name']+'"',  ",".join("?" * len(ids)))
    print(sql)
    res = cur.execute(sql, ids)
    res = [item for item in res.fetchall()]
    for item in res:
        new_list = []
        ent = json.loads(item[2])
        label = json.loads(item[1])
        for ent_item in ent:
            if ent_item[0] == data['type'] and ent_item[1] == data['name']:
                if data['oper'] == 0:
                    label[ent_item[2]:ent_item[3]+1] = ['O']*(ent_item[3]+1-ent_item[2])
                    continue
                else:
                    ent_item[0] = CHANGE_PATH[data['type']]
            new_list.append(ent_item)
        cur.execute(f'update {data_name} set entitys=?, label=? where id=?',
                    (json.dumps(new_list, ensure_ascii=False), json.dumps(label, ensure_ascii=False), item[0]))
        conn.commit()
        print(f"id为{item[0]}的记录更新{'成功' if conn.total_changes > 0 else '失败'}")
def find_selected(data_name):
    conn, cur = open_db('source')
    sql = f'select * from {data_name} where selected=1 and status!=2'
    res = cur.execute(sql)
    res = [row for row in res.fetchall()]
    conn.commit()
    conn.close()
    return res

def find_unlabel(data_name):
    conn, cur = open_db('source')
    sql = f'select * from {data_name} where selected=0 and status=0 and length(content)<202'
    res = cur.execute(sql)
    res = [row for row in res.fetchall()]
    conn.commit()
    conn.close()
    return res

def find_train_data(data_name, ids):
    conn, cur = open_db('source')
    sql = "select content, user_label from {} where id in({})".format(data_name, ','.join("?"*len(ids)))
    res = cur.execute(sql, ids)
    res = [row for row in res.fetchall()]
    return res

def find_loop_data(data_name, loop):
    conn, cur = open_db('source')
    sql = "select * from {} where loop={}".format(data_name, loop)
    res = cur.execute(sql)
    res = [row for row in res.fetchall()]
    cur.close()
    conn.close()
    return res


def find_lower_loop(data_name, loop):
    sql = f'select loop from {data_name} where loop < {loop} and loop >= 0 GROUP BY loop'
    conn, cur = open_db('source')
    res = cur.execute(sql)
    res = [row[0] for row in res.fetchall()]
    cur.close()
    conn.close()
    return res

def find_all_loop_entity(data_name):
    conn, cur = open_db('source')
    sql = f'select loop,id,entitys,content from {data_name} where loop!=-1'
    res = cur.execute(sql)
    res = [row for row in res.fetchall()]
    cur.close()
    conn.close()
    return res

def find_loop_train_data(data_name, loop):
    conn, cur = open_db('source')
    sql = "select content, label from {} where loop={}".format(data_name, loop)
    res = cur.execute(sql)
    res = [row for row in res.fetchall()]
    cur.close()
    conn.close()
    return res

def reset():
    conn, cur = open_db('source')
    sql = 'update zhs_0001 set status=0'
    cur.execute(sql)
    conn.commit()
    conn.close()

def reset1():
    conn, cur = open_db('source')
    sql = 'update tangs set loop=-1, status=0, selected=0'
    cur.execute(sql)
    sql = 'delete from train_record'
    cur.execute(sql)
    sql = 'delete from operations'
    cur.execute(sql)
    conn.commit()
    conn.close()

# reset1()

def find_loopData_upID(data_name, loopID):
    conn, cur = open_db('source')
    sql = f"select loop from {data_name} where loop >= {loopID} GROUP BY loop"
    # 获取查询结果
    cur.execute(sql)
    rows = cur.fetchall()
    # 打印每个分组的loopID和记录数量
    res = [row[0] for row in rows]
    cur.close()
    conn.close()
    return res
#######################记录表###################
def insert_record(data):
    conn, cur = open_db('source')
    sql = 'insert into train_record (epoch, trainlog, al_epoch_samples, data_name, vallog) values (?,?,?,?,?) '
    cur.execute(sql, (data[0], json.dumps(data[1]["trainlog"]), json.dumps(data[2]), data[3], json.dumps(data[1]['vallog'])))
    conn.commit()
    conn.close()

def get_all_record(data_name):
    conn, cur = open_db('source')
    sql = 'select * from train_record where data_name=?'
    res = cur.execute(sql, (data_name, ))
    res = [row for row in res.fetchall()]
    conn.close()
    return res

def get_labeledorunlabel(data_name, ids, status):
    conn, cur = open_db('source')
    sql = 'select * from {} where status={} and id in ({})'.format(data_name, status, ','.join("?"*len(ids)))
    res = cur.execute(sql, ids)
    res = res.fetchall()
    cur.close()
    conn.close()
    return len(res)

def get_all_labeledorunlabel(data_name, status):
    conn, cur = open_db('source')
    sql = 'select * from {} where status={}'.format(data_name, status)
    res = cur.execute(sql)
    res = res.fetchall()
    cur.close()
    conn.close()
    return len(res)

def update_record(loop, name, data):
    conn, cur = open_db('source')
    sql = f'update train_record set trainlog=? where epoch={loop} and data_name={json.dumps(name)}'
    cur.execute(sql, (json.dumps(data), ))
    conn.commit()
    cur.close()
    conn.close()

########################操作记录表#######################
def insert_oper_record(data):
    conn, cur = open_db('source')
    sql = 'insert into operations (source,target,oper_type,sample_id,loop,source_name,target_name) values (?,?,?,?,?,?,?) '
    cur.execute(sql, (json.dumps(data['source']), json.dumps(data['target']),
                      data['type'], data['id'], data['loop'], data['sourceName'], data['targetName']))
    conn.commit()
    cur.close()
    conn.close()

def query_operation(sample_id=None,loop=None):
    conn, cur = open_db('source')
    if sample_id is None and loop is None:
        sql = 'select * from operations'
        res = cur.execute(sql)
    elif sample_id is not None and loop is None:
        sql = 'select * from operations where sample_id = (?)'
        res = cur.execute(sql, (sample_id, ))
    elif sample_id is None and loop is not None:
        sql = 'select * from operations where loop = (?)'
        res = cur.execute(sql, (loop,))
    else:
        sql = 'select * from operations where sample_id = (?) and loop=(?)'
        res = cur.execute(sql, (sample_id,loop))
    res = [row for row in res.fetchall()]
    conn.close()
    return res

def query_grouped_sample(loop, data_name):
    conn, cur = open_db('source')
    sql = f'select sample_id from operations where loop={loop} and data_name={json.dumps(data_name)} group by sample_id'
    res = cur.execute(sql)
    res = [row[0] for row in res]
    cur.close()
    conn.close()
    return res

def query_grouped_loop(data_name):
    conn, cur = open_db('source')
    sql = f'select loop from operations where data_name={json.dumps(data_name)} group by loop'
    res = cur.execute(sql)
    res = [row[0] for row in res]
    cur.close()
    conn.close()
    return res

def find_frequency(name,data_name=None):
    conn, cur = open_db('source')
    sql = f'select COUNT(*) from operations where source_name=(?) or target_name=(?) and data_name={json.dumps(data_name)}'
    res = cur.execute(sql, (name, name))
    res = res.fetchall()[0][0]
    if res == 0:
        res = 1
    cur.close()
    conn.close()
    return res

def count_sample_record(sample_id, data_name):
    conn, cur = open_db('source')
    sql = f'select COUNT(*) from operations where sample_id={sample_id} and data_name={json.dumps(data_name)}'
    res = cur.execute(sql)
    res = res.fetchall()[0][0]
    cur.close()
    conn.close()
    return res


#################################################################
######################操作entities表##############################
#################################################################
def reset_entities_record():
    conn, cur = open_db('source')
    cur.execute("delete from entities")
    conn.commit()
    cur.close()
    conn.close()
def insert_entity(entities, loop):
    conn, cur = open_db('source')
    for item in entities:
        try:
            cur.execute("insert into entities(name, real_name, ids, weight, type) values (?,?,?,?,?) ",
                    (item[0], item[1], json.dumps([loop, ",".join(map(str, item[2]))]), json.dumps([loop, item[3]]), item[4]))
        except sqlite3.Error as e:
            cur.execute("update entities set ids=ids||';'||?, weight=weight||';'||? where name=?",
                        (json.dumps([loop, ",".join(map(str, item[2]))]), json.dumps([loop, item[3]]), item[0]))
    conn.commit()
    cur.close()
    conn.close()

def query_all_entities():
    conn, cur = open_db('source')
    res = cur.execute("select * from entities")
    res = [item for item in res.fetchall()]
    return res

def query_entities_by_type(type):
    conn, cur = open_db('source')
    res = cur.execute("select * from entities where type=?", (type, ))
    res = res.fetchall()
    cur.close()
    conn.close()
    return res

def get_weight_by_name(name):
    conn, cur = open_db('source')
    res = cur.execute("select weight from entities where name=?", (name,))
    try:
        res = res.fetchone()[0]
        res = res.split(";")
        weight_obj = [eval(e) for e in res]
        weight = 0
        for e in weight_obj:
            weight += e[1]
    except TypeError:
        weight = 1
    cur.close()
    conn.close()
    return weight


#***********************************操作时间记录表**********************************#
## 插入记录
def insert_time_record(data_name, loop, time_record):
    conn, cur = open_db('source')
    cur.execute("insert into label_time(data_name, loop, time) values (?,?,?)",
                      (data_name, loop, time_record))
    conn.commit()
    cur.close()
    conn.close()


def get_all_time(data_name):
    conn, cur = open_db('source')
    res = cur.execute("select * from label_time where data_name=?", (data_name, ))
    res = [item for item in res.fetchall()]
    cur.close()
    conn.close()
    return res

def reset_time_record():
    conn, cur = open_db('source')
    cur.execute("delete from label_time")
    conn.commit()
    cur.close()
    conn.close()

def get_entity_num(entity):
    conn, cur = open_db('source')
    res = cur.execute(f"select count(*) from alltangs where entitys like '%{entity}%' and loop > 0")
    res = res.fetchall()
    return res[0][0]

