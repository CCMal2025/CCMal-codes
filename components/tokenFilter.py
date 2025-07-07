from collections import Counter
from typing import Union, FrozenSet, Set


class TokenFilter:
    def __init__(self, threshold=0.7, version = 42):
        self.malware_tokens = []  # Tokens of malware
        self.malware_tokens_set = []  # Tokens set of malware
        self.malware_tokens_set_cnt = []
        self.mal_func_path = []
        self.threshold = threshold
        self.version = version

    @staticmethod
    def jaccard_distance(counter1: Counter, set1: Union[FrozenSet, Set], counter2: Counter,
                         set2: Union[FrozenSet, Set]) -> float:
        intersection_size = sum((min(counter1[x], counter2[x]) for x in set1.intersection(set2)))
        union_size = sum((max(counter1[x], counter2[x]) for x in set1.union(set2)))

        similarity = intersection_size / union_size if union_size != 0 else 0

        return similarity

    def insert(self, malware_token: Counter, mal_func_path: str, malware_token_cnt: int):
        self.malware_tokens.append(malware_token)
        self.malware_tokens_set_cnt.append(malware_token_cnt)
        self.malware_tokens_set.append(frozenset(malware_token.keys()))
        self.mal_func_path.append(mal_func_path)

    def query(self, token: Counter, overwrite_threshold: float | None = None) -> tuple[list[tuple[str, float]], float]:
        token_set = set(token.keys())
        sim_func_path = []
        max_sim = 0
        token_cnt = token.total()
        threshold = self.threshold if overwrite_threshold is None else overwrite_threshold
        for mal_token, mal_token_set, mal_func_id, mal_cnt in zip(self.malware_tokens, self.malware_tokens_set,
                                                                  self.mal_func_path, self.malware_tokens_set_cnt):
            if threshold < token_cnt / mal_cnt < 1 / threshold:
                sim = self.jaccard_distance(token, token_set, mal_token, mal_token_set)
                if sim > threshold:
                    sim_func_path.append((mal_func_id, sim))
                max_sim = max(sim, max_sim)
        return sim_func_path, max_sim

    def query_with_max_sim(self, token: Counter):
        token_set = set(token.keys())
        max_sim = 0
        max_sim_func_id = None
        sim_func_path = []
        for mal_token, mal_token_set, mal_func_id in zip(self.malware_tokens, self.malware_tokens_set,
                                                         self.mal_func_path):
            sim = self.jaccard_distance(token, token_set, mal_token, mal_token_set)
            if sim > self.threshold:
                sim_func_path.append((mal_func_id, sim))
            if sim >= max_sim:
                max_sim_func_id = mal_func_id
                max_sim = sim
        return sim_func_path, max_sim, max_sim_func_id
