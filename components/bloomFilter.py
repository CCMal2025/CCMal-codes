import math
from typing import Iterable

import numpy as np
from bloom_filter2 import BloomFilter


class NSFBF:

    def __init__(self, vector_len, N=10000, tile_cnt=5, trail_cnt=10, seed=42, version=42):
        self.tile_cnt = tile_cnt
        self.trail_cnt = trail_cnt
        # self.rebuild = rebuild
        self.padding = math.ceil(vector_len / tile_cnt) * tile_cnt - vector_len
        self.threshold = None
        self._filters = []
        for _ in range(trail_cnt):
            filter_row = []
            for _ in range(tile_cnt):
                filter_row.append(BloomFilter(max_elements=N, error_rate=1e-5))
            self._filters.append(filter_row)

        self._main_filter = BloomFilter(max_elements=N, error_rate=1e-5)
        self.seed = [seed + i for i in range(trail_cnt)]
        self.version = version

    @staticmethod
    def convert_vector_to_number(vector: np.ndarray):
        return int(''.join(vector.astype(int).astype(str)), 2)

    def _encode(self, vector: np.ndarray, trail):
        new_v = np.append(vector, np.zeros(self.padding))
        rng = np.random.RandomState(seed=self.seed[trail])
        rng.shuffle(new_v)
        # split vector to tiles
        tiles = np.array_split(new_v, self.tile_cnt)
        return [self.convert_vector_to_number(tile) for tile in tiles]

    def insert(self, vector: np.ndarray):
        self._main_filter.add(self.convert_vector_to_number(vector))
        for trail in range(self.trail_cnt):
            encode_v = self._encode(vector, trail)
            for tile in range(self.tile_cnt):
                self._filters[trail][tile].add(encode_v[tile])

    def query(self, vector: np.ndarray):
        max_unmatched = 0
        if self.convert_vector_to_number(vector) in self._main_filter:
            return 0
        for trail in range(self.trail_cnt):
            unmatched_cnt = 0
            encode_v = self._encode(vector, trail)
            for tile in range(self.tile_cnt):
                if encode_v[tile] not in self._filters[trail][tile]:
                    unmatched_cnt += 1
            if unmatched_cnt > self.threshold:
                return unmatched_cnt
            max_unmatched = max(max_unmatched, unmatched_cnt)
        return max_unmatched

    def construct(self, construct_vecs: Iterable[np.ndarray], threshold):
        self.threshold = threshold
        for vec in construct_vecs:
            self.insert(vec)

    def detect(self, target_vec: np.ndarray, overwrite_threshold = None):
        if overwrite_threshold is None:
            if self.threshold is None:
                raise Exception("NSFBF not constructed")
            threshold = self.threshold
        else:
            threshold = overwrite_threshold

        return self.query(target_vec) <= threshold
