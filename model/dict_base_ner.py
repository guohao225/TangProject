import pprint
import logging
logging.basicConfig(level = logging.INFO, format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class Trie(object):
    def __init__(self):
        self.trie = {}
        self.depth = 0

    def add_node(self, entitys, entity_type):
        for word in entitys:
            word = word.lower()
            self.depth = max(len(word), self.depth)
            tree = self.trie
            for char in word:
                if char in tree:
                    tree = tree[char]
                else:
                    tree[char] = {}
                    tree = tree[char]
            if 'type' in tree:
                logging.info("entity: {} is '{}' and '{}', save {} (*_*) ...".format(word, tree['type'], entity_type, tree['type']))
                continue
            tree['type'] = entity_type

    def search_word(self, word):
        tree = self.trie
        step = 0
        for char in word:
            if char in tree:
                tree = tree[char]
                step += 1
                if 'type' in tree:
                    return step, tree['type']
            else:
                break
        return 1, None


class NER(object):
    def __init__(self, ner_dict):
        """
        采用自定义词典进行NER
        :param ner_dict:

        ner_dict = {"LOC": ["河南", "洪洞县", "张家庄", "西门"],
                    "PER": ["小明", "小红", "张三林", "欧阳李丹", "西门", "JACk"]}

        """
        self.trie = Trie()
        self.add_nodes(ner_dict)

    def add_nodes(self, ner_dict):
        for entity_type, entitys in ner_dict.items():
            self.trie.add_node(entitys, entity_type)

    def tag(self, text):
        ner_results = []
        idx = 0
        while idx < len(text):
            words = text[idx: idx+self.trie.depth].lower()
            step, ner_type = self.trie.search_word(words)
            if ner_type:
                ner_results.append({"text": text[idx:idx+step], "offsets": [idx, idx+step], "type": ner_type})
            idx += step

        pprint.pprint(ner_results)

        return ner_results

