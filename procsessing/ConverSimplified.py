# -*- coding = utf-8 -*-
# @Time:
# @Author: GH
import zhconv


def convert_simplified(sen_list):
    if isinstance(sen_list, list):
        res_list = [zhconv.convert(sentence, 'zh-cn') for sentence in sen_list]
    else:
        res_list = zhconv.convert(sen_list, 'zh-cn')
    return res_list

