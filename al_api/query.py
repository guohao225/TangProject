# -*- coding:utf-8 -*-

import json
import os
import re
from selenium import webdriver
import urllib.request as urllib
from urllib.parse import quote as quote

import requests
from bs4 import BeautifulSoup
import al_api.utils as tools
from untils import DictMaper, PathManger
from untils import DataBase as db
import pandas as pd

WORD_QUERY_BASE_URL = r'https://dict.baidu.com/s?'
POEM_QUERY_BASE_URL = r'https://so.gushiwen.cn/search.aspx?value={0}&valuej={1}'
##加载词典
dic_maper = DictMaper.Trie()
dic_maper.load_dic(os.path.join(PathManger.get_root_path(), "data/vocab/places.txt"), "LOC")
dic_maper.load_dic(os.path.join(PathManger.get_root_path(), "data/vocab/names.txt"), "PER")
dic_maper.load_dic(os.path.join(PathManger.get_root_path(), "data/vocab/times.txt"), "ORG")

def word_query(word):
    word = quote(word, 'utf8')
    url = f"{WORD_QUERY_BASE_URL}wd={word}&from=zici"
    res = urllib.urlopen(url, timeout=1)
    content = res.read()
    soup = BeautifulSoup(content, "html.parser", from_encoding='utf-8')
    content_div = soup.find('div', class_='tab-content')
    if content_div is None:
        content_div = soup.find('div', class_='poem-list-item')
    return content_div


# 获取实体的出现的频率
def entity_frequency():
    entitys = tools.get_entities()
    entity_type = entitys.groupby("type")
    res = []
    for type, value in entity_type:
        if type == "B-LOC":
            serie = {'name': "地名"}
        else:
            serie = {'name': "人名"}
        data = []
        p_group = value.groupby('entity')
        for key, ent in p_group:
            data.append({"name": key, "value": len(ent)})
        serie["data"] = data[0:100]
        res.append(serie)
    return res


def entity_frequency_antv():
    entitys = tools.get_entities()
    entity_type = entitys.groupby("type")
    print(len(entity_type))
    res = []
    id = 0
    linkBeg = 0
    for type, value in entity_type:
        p_group = value.groupby('entity')
        for key, ent in p_group:
            if type == "B-LOC":
                cluster = 0
            else:
                cluster = 1
            res.append({
                "name": key,
                "type":cluster,
                "weight":len(ent),
                "cluster": linkBeg
            })
        linkBeg += len(res)
    return res


def query_entity_by_dic(text, max_len):
    entity = dic_maper.fmm(text)
    label = ['O' for index in range(0, max_len)]
    for item in entity:
        for begin in range(item[1], item[2]+1):
            if begin == item[1]:
                label[begin] = 'B-'+item[0]
            else:
                label[begin] = 'I-'+item[0]
    # for item in entity:
    #     print(label[item[1]:item[2]+1])
    return label, entity

def query_all_poems():
    all_poems = db.find_data_list('alltangs')
    for item in all_poems:
        content = json.loads(item[3])
        content = "".join(content)
        label, entitys = query_entity_by_dic(content, 200)
        ## 更新数据库
        db.update_data_obj('alltangs', [item[0]], 'label', [label])
        db.update_data_obj('alltangs', [item[0]], 'entitys', [entitys])

# query_all_poems()
# res = query_entity_by_dic('欧阳文忠公尝问余：“琴诗何者最善？答以退之听颖师琴诗最善。公曰：此诗最奇丽，然非听琴，乃听琵琶也。余深然之。建安章质夫家善琵琶者，乞为歌词。余久不作，特取退之词，稍加隐括，使就声律，以遗之云。昵昵儿女语，灯火夜微明。恩怨尔汝来去，弹指泪和声。忽变轩昂勇士，一鼓填然作气，千里不留行。回首暮云远，飞絮搅青冥。众禽里，真彩凤，独不鸣。跻攀寸步千险，一落百寻轻。烦子指间风雨，置我肠中冰炭，起坐不能平。推手从归去，无泪与君倾。', 200)
# print(res[1])
def query_poem_tip(key):
    value = quote(key, 'utf8')
    valuej = quote(key[0], 'utf8')
    global POEM_QUERY_BASE_URL
    POEM_QUERY_BASE_URL = POEM_QUERY_BASE_URL.format(value, valuej)
    res = urllib.urlopen(POEM_QUERY_BASE_URL)
    content = res.read()
    soup = BeautifulSoup(content, "html.parser", from_encoding='utf-8')
    res = soup.find("img", alt="详情")
    if res == None:
        return "未找到注释"
    detail = res.parent
    href = detail.get("href")
    res = urllib.urlopen(href)
    content = res.read()
    soup = BeautifulSoup(content, "html.parser", from_encoding='utf-8')
    node = soup.find(href=lambda x: x and 'javascript:fanyiShow' in x)
    if node is None:
        return "未找到注释"
    href = node.get("href")
    matches = re.findall(r"'(.*?)'", href)[0]
    note_URL = f'https://so.gushiwen.cn/nocdn/ajaxfanyi.aspx?id={matches}'
    res = urllib.urlopen(note_URL)
    content = res.read()
    soup = BeautifulSoup(content, "html.parser", from_encoding='utf-8')
    text = soup.text
    return text

# query_poem_tip("将进酒李白")
# res = query_poem_tip("采薇佚名")
# print(res)