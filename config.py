import os.path

import tomlkit

config = {}

def init_toml(config_file="config.toml"):
    doc = tomlkit.document()

    doc.add("clear_cache", False)
    doc.add("remove_mal_log", True)
    doc.add("mal_file_logs", "mal.jsonl")

    # threshold
    threshold = tomlkit.document()
    threshold.add("pfbf", 1)
    threshold.add("token", 0.8)
    threshold.add("syntax", 0.8)

    doc.add("threshold", threshold)

    # pfbf
    pfbf = tomlkit.document()
    pfbf.add("tile_cnt", 2)
    pfbf.add("seed", 42)

    doc.add("pfbf", pfbf)

    # resource
    resource = tomlkit.document()
    resource.add("precise_dataset", "resource/precise_dataset.db")

    doc.add("resource", resource)

    # experiments
    experiment = tomlkit.document()
    experiment.add("dump_fn", False)
    experiment.add("dump_pn_result", True)

    doc.add("experiment", experiment)
    with open(config_file, "w") as f:
        tomlkit.dump(doc, f)




def load_config_from_file(config_file="config.toml"):
    global config
    if not os.path.exists(config_file):
        init_toml()
    with open(config_file, "r") as f:
        config = tomlkit.load(f)

load_config_from_file()

if __name__ == "__main__":
    print(config)