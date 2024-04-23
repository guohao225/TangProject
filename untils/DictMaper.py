class TrieNode:
    """Trie 树的节点"""
    def __init__(self, c):
        #  保存字符
        self.c = c
        # 是否是一个词的终止字
        self.is_end = False
        self.type = "B-LOC"
        # 保存子节点，key 为字，value 为节点
        self.children = {}


class Trie(object):
    """Trie 树"""

    def __init__(self):
        """根节点，空的，不保存任何字符"""
        self.root = TrieNode('\x01')

    def add(self, w, type):
        """插入词，构建 Trie 树"""
        n = self.root
        # 插入到合适的节点中
        for c in w:
            if c in n.children:
                n = n.children[c]
            else:
                nn = TrieNode(c)
                n.children[c] = nn
                n = nn
        # 词的最后一个字所对应的节点
        n.is_end = True
        n.type = type

    def fmm(self, s):
        """正向最大匹配(forward maximum matching)算法"""
        results = []
        slen = len(s)
        i = 0
        while i < slen:
            n = self.root
            w = ''
            for j in range(i, slen):
                c = s[j]
                if c in n.children:
                    n = n.children[c]
                    w += c
                else:
                    if n.is_end:
                        # 如果匹配出一个词，则从该词的结束位置开始下一次匹配
                        results.append([n.type, j-len(w), j-1, w])
                        i = j - 1
                    break
            i += 1
        return results

    def load_dic(self, file_name, type):
        with open(file_name, encoding="utf8") as f:
            for line in f:
                self.add(line.strip(), type)
        print(f"load {type} success")
