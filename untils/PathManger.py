# -*- coding = utf-8 -*-
# @Time:
# @Author: GH
import os
import sys


def get_root_path():
    if 'ipykernel' in os.environ.get('PYCHARM_HOSTED', ''):
        print('当前代码在PyCharm中以Jupyter Notebook模式运行')
        return os.path.abspath('.')
    elif 'ipykernel' in os.environ.get('VIRTUAL_ENV', ''):
        print('当前代码在虚拟环境中以Jupyter Notebook模式运行')
        return os.path.abspath('.')
    elif 'ipykernel' in sys.modules:
        print('当前代码在Jupyter Notebook中运行')
        return os.path.abspath('.')
    debug_evn = dict((a, b) for a, b in os.environ.items()
                     if a.find('IPYTHONENABLE') >= 0)
    if len(debug_evn) > 0:
        root_path = sys.path[2]
    elif getattr(sys, 'frozen', False):
        root_path = os.gecwd()
    else:
        root_path = sys.path[1]
    return root_path

def get_bert_path():
    root = get_root_path()
    bert_path = os.path.join(root, 'checkpoints/guwenbert-base-tf2')
    return bert_path