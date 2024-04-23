# @time:2023/3/15 15:19
# @functional:
import pandas
def concat_word_label(sentence, label):
    sen_list = []
    lab_list = []
    for i in range(len(sentence)):
        str_list = list(sentence[i])
        if len(label[i]) < len(str_list):
            label[i] += ['O' for item in range(len(str_list)-len(label[i]))]
        if len(label[i]) > len(str_list):
            del label[i][len(str_list):]
        sen_list += str_list
        lab_list += label[i]
    return sen_list, lab_list

def word_label_corresponding(data):
    word =[]
    label=[]
    for item in data:
        sen_list, lab_list = concat_word_label(item['paragraphs'], item['labels'])
        sen_list.append('#')
        lab_list.append('#')
        word+=sen_list
        label+=lab_list
    del label[-1]
    del word[-1]
    return word, label

