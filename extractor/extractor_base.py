import collections
import json
import os
from abc import abstractmethod
from typing import List, Counter, Tuple

import numpy as np

from .utils import Tree

with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "keywords.json")) as f:
    keyword_conf = json.load(f)


def keywords_len(lang: str):
    return len(keyword_conf[lang])


class Extractor:

    def __init__(self, code: bytes, language_str):
        if code:
            self.tree = Tree(code, language_str)
            self.lang = {
                "bash": "sh",
                "javascript": "js",
                "python": "py"
            }[language_str]
        else:
            self.tree = None
            print("Code is None")

    @property
    @abstractmethod
    def token_type_black_list(self) -> Tuple:
        pass

    @property
    @abstractmethod
    def token_type_str_list(self) -> Tuple:
        pass

    def keyword_vector(self):
        token = self.token()
        return np.array([1 if token[keyword] > 0 else 0 for keyword in keyword_conf[self.lang]])

    def token(self) -> Counter:
        tokens_counter = collections.Counter()
        if self.tree is None:
            return tokens_counter
        for node in filter(lambda node: len(node.children) == 0, self.tree):
            if len(node.children) == 0:
                if node.type not in self.token_type_black_list:
                    # print(node, node.text)
                    tokens_counter.update([node.text.decode('utf-8', "ignore")])
                elif node.type in self.token_type_str_list:
                    # print(node, b"")
                    tokens_counter.update([""])
        return tokens_counter

    def syntax_seq(self) -> List:
        seq = []
        for node in self.tree:
            if node.type not in self.token_type_black_list:
                seq.append(node.type)
        return seq