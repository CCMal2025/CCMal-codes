import Levenshtein


def jaro_sim(seq1, seq2):
    return Levenshtein.jaro(seq1, seq2)

def levenshtein_sim(seq1, seq2):
    return Levenshtein.ratio(seq1, seq2)

class SyntaxFilter:
    def __init__(self, threshold=0.7, method="jaro"):
        self.malware_seq = []
        self.mal_func_path = []
        self.mal_func_dict = {} # Test only, Remove in parallel
        self.threshold = threshold
        self.method = method



    def sim(self, seq1, seq2):
        return {
            "jaro": jaro_sim,
            "levenshtein": levenshtein_sim
        }[self.method](seq1, seq2)

    def insert(self, malware_seq, malware_func_path):
        self.malware_seq.append(malware_seq)
        self.mal_func_path.append(malware_func_path)
        self.mal_func_dict[malware_func_path] = malware_seq # Test only, Remove in parallel

    def query(self, seq, target_func_path_list):
        sim_func_path = []
        # max_sim = 0
        for mal_func_path in target_func_path_list:
            mal_seq = self.mal_func_dict[mal_func_path]
            sim = self.sim(seq, mal_seq)
            if sim > self.threshold:
                sim_func_path.append(mal_func_path)
            # max_sim = max(max_sim, sim)
        # print(max_sim)
        return sim_func_path

class SyntaxFilter2:
    method = "jaro"
    def __init__(self, threshold=0.7):
        self.threshold = threshold
        pass

    def sim(self, seq1, seq2):
        return {
            "jaro": jaro_sim,
            "levenshtein": levenshtein_sim
        }[self.method](seq1, seq2)

    def query(self, mal_seq, seq, overwrite_threshold=None):
        if overwrite_threshold is None:
            overwrite_threshold = self.threshold
        sim = self.sim(seq, mal_seq)
        return sim > overwrite_threshold, sim
