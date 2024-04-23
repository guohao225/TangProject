import main
import untils.Config as cof
import numpy as np
import untils.DataBase as db
import ast


def get_model_config():
    config = main.configure.get_train_config(use_to_web=True)
    return config


def set_model_config(data):
    try:
        main.configure.set_config(data, save_to_file=True)
        return 1
    except Exception:
        return 0


def reset_model_config():
    try:
        cof.reset_config_file()
        return 1
    except Exception:
        return 0


# 开始训练模型--并以配置参数命名保存参数的文件
def begin_train(status=False):
    if status:
        main.train(True)
    else:
        main.stop_fun()


def get_train_data():
    x = main.X
    y = main.EPOCH_LOG.tolist()
    return x, y

def get_baseline_log():
    id = main.configure.generate_baseline_name(sep="#")
    conn, cursor = db.create_lit_obj()
    x, y = db.get_baseline_log(id, cursor)
    db.close_connection(conn)
    x = ast.literal_eval(x)
    x = x.index(0, 0)
    y = ast.literal_eval(y)
    y = y.index(0, 0)
    return x, y

# def file_precess(file):



# get_baseline_log()
# begin_train(True)