import re
# import jieba
import tensorflow as tf

def proces_dict():
    fp = open("./datasets/all_data.txt", 'r', encoding='utf8')
    texts = []
    for line in fp:
        head_name, tail_name, relation, text = re.split(r'\t', line)
        texts.append(text.strip())
    with open('dict.txt', 'w+', encoding='utf8') as q:
        for line in texts:
            line = line.replace(" ", "")
            line = line.replace('\t', "")
            q.write(line+"\n")

def fenci():
    newList = []
    jieba.enable_paddle()
    fp = open("./datasets/all_data.txt", 'r', encoding='utf8')
    for line in fp:
        line = line.strip()
        line = line.replace(" ", "")
        line = line.replace('\t', "")
        seg_list = jieba.cut(line, cut_all=False)
        seg_list = ",".join(seg_list)
        newList.append(seg_list)
    with open('fenci.txt', 'w+', encoding='utf8') as q:
        for line in newList:
            line = line.replace(" ", "")
            line = line.replace('\t', "")
            q.write(line + "\n")

def test():
    import tensorflow as tf

    # 假设A、B和C是相同维度的三维张量
    # 创建示例数据，你需要替换成你的实际数据
    A = tf.constant([[[1, 2, 3],
                        [4, 5, 6]],
                     [[7, 8, 9], [10, 11, 12]]], dtype=tf.float32)

    B = tf.constant([[[13, 14, 15], [16, 17, 18]],
                     [[19, 20, 21], [22, 23, 24]]], dtype=tf.float32)

    C = tf.constant([[[25, 26, 27], [28, 29, 30]],
                     [[31, 32, 33], [34, 35, 36]]], dtype=tf.float32)

    # 获取形状
    shape = A.shape
    print(A.shape)

    # 创建一个新的张量D，用于存储结果
    D = tf.Variable(tf.zeros(shape, dtype=tf.float32))

    # 在第1维上进行替换
    for i in range(shape[0]):
        if i % 2 == 0:
            D = tf.concat([D, tf.expand_dims(A[i], axis=0)], axis=0)
        else:
            D = tf.concat([D, tf.expand_dims(C[i], axis=0)], axis=0)

    # 去除多余的部分
    D = D[1:]

    # 打印结果
    print(D.numpy())


test()
