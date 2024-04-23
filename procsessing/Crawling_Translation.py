import json

import requests
import re

headers = {
    'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36"
}


def craw_poet(type):
    base_url =f"https://so.gushiwen.cn/gushi/{type}"
    response = requests.get(base_url, headers=headers)
    text = response.text
    sons_frame = re.findall(r'<span><a href="(.*)" target="_blank">.*</a>[\(]?.*[\)]?</span>', text)
    sons = set(sons_frame)
    print(sons_frame)
    sons_base_url = 'https://so.gushiwen.cn'
    for url in sons:
        print(url)
        sons_url = sons_base_url+"/shiwenv_9306064f2630.aspx"
        sons_response = requests.get(sons_url, headers=headers)
        data = sons_response.text
        title = re.findall(r'<h1 style="font-size:20px; line-height:22px; height:22px; margin-bottom:10px;">(.*)</h1>', data)[0]
        poemdata = re.findall(r'<h1 style="font-size:20px; line-height:22px; height:22px; margin-bottom:10px;">(.*)猜您喜欢', data, re.DOTALL)[0]
        author = re.findall(r'<p class="source"><a href=".*">(.*)</a>.*<a href=".*">(.*)</a></p>', poemdata)
        poem = re.findall(r'<div class="contson" id=".*">(.*)</div>', poemdata, re.DOTALL)
        print(poemdata)
        print(title)
        print(author)
        print(poem)
        break




# def parse_page(title, author):
#     url = concat_url(title, author)
#     headers = set_header("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
#                          "(KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36")
#     response = requests.get(url, headers=headers)
#     text = response.text
#     print(text)
#     id = re.findall(r'<span style="color:#B00815;line-height:100%;">(.*)</span>', text)[0]
#     print(id)
#     # url_next = 'https://so.gushiwen.cn//nocdn/ajaxshiwencont.aspx?id=' + id + '&value=yi'
#     # response1 = requests.get(url_next, headers=headers)
#     # text1 = response1.text
#     # translation = re.findall(r'<span style="color:#af9100;">(.*)<br /></span></p>', text1)
#     # print(translation)
#     # if translation == '':
#     #     return []
#     # return translation


# def add_translation(json_data, title_field, author_field, trans_flied_name='translation'):
#     if isinstance(json_data, dict):
#         raise Exception('参数非json数据')
#     if len(json_data) == 0:
#         print("数据为空")
#         return
#     for item in json_data:
#         trans = parse_page(item[title_field],item[author_field])
#         item[trans_flied_name] = trans


# with open('../source/test.json', 'r', encoding='utf8') as fp:
#     data = json.load(fp)
# add_translation(data, 'title', 'author')
# with open('../source/test_tran.json', 'w', encoding="utf8") as fp:
#     json.dump(data, fp, ensure_ascii=False, indent=4)
craw_poet('tangshi.aspx')