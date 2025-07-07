# CCMal

## Installation

### requirements

- Linux (Windows not support)
- Python 3.12
- Redis 7.4 (lower versions may work)
- Celery (included in requirements.txt)
- Precise Dataset: A sqlite3 database containing malicious files and codes

```bash
pip install -r reqirements.txt
```

## Precise Dataset

TBD


## Launch CCMal

### Start Redis

CCMal depends on docker. We use `7.4.3` in our experiments. Lower versions might work. Make sure Redis listens port `24779`.

```bash
docker run -p 24779:6379 -itd redis/redis:7.4.3
```

### Configuation

Run ``python config.py`` or refering to `config.example.toml` to config CCMal. You can keep most of the configs to default except `precise_dataset`, which should set to the path to the Precise Dataset

### Initialization

CCMal need to initialize before first run. We suggest to re-run the initialization in the following situation:

- After the update of Precise Dataset.
- Changing configs(except thresholds) of PFBF, TokenFilter and SyntaxFilter. Note that it is no need to re-run initialization when only changing thresholds.

```bash
python3 initialization.py
```

### Start Celery Worker

Celery workers should run before main detect thread. It controls the parallelism of CCMal and schedule the detection task.

Feel free to limit the concurrency of the following command to avoid crashes. We suggest to set it to `1.5*cpu_count()`

```bash
Celery -A celery_task worker -l warning --concurrency=48 -Ofair
```

### Detect Malicious Package

You can detect malicious packages by editing the `main.py` or calling function `detect`

```python
detect(target_package_path_list)
```

The result will be log in `mal.jsonl` in default configuration.

### Detect Malicious Package Remote

We provide `server.py` for detection remotely. Run command below, a detect server will be launched at port `8000`

```bash
python3 server.py
```

#### Method 
```http request
POST /detect/ccmal?bloom=1&token=0.8&syntax=0.8
```
- body: list of `target_package_path_list`
- args: control the threshold of each component. bloom for `PFBF`, token for `tokenFilter`, syntax for `syntaxFilter`

**Response**
```json
{"run_time": 8.074663400650024, "malicious": [0], "malicious_files": {"0": ["index.js"]}}
```
- `run_time` CCMal run_time. (Runtime of function `detect`)
- `malicious` The index list of malicious packages in the list given by Body. `0` indicates the index `0` of `target_package_path_list` is malicious.
- `malicious_file` A dict with the detailed information of malicious files. The key is the index of the `target_package_path_list`, and the value is a list of malicious file path in the corresponding pacakge.


## Run CCMal In Docker

Run CCMal in Docker will **automatically** launch Redis and Celery and provide a http server interface for detecting malicious code. However, you should manually mount the target packages to docker. 

### Build Docker

We provide `dockerfile` to build docker.
```bash 
docker build . -t ccmal/ccmal
```

### Detect

Same as **Detect Malicious Package Remote**.