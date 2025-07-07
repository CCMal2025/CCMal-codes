import http
import json
import time

from flask import Flask, request

import main

app = Flask(__name__)

@app.route('/detect', methods=['GET'])
def ping():
    return json.dumps({
        "npm": ["ccmal-npm"],
        "pypi": ["ccmal-pypi"],
    })

@app.route('/detect/<method>', methods=['POST'])
def detect(method):
    if method not in [
        'ccmal-npm',
        'ccmal-pypi',
    ]:
        return "", http.HTTPStatus.BAD_REQUEST
    print("Detect initial")

    target_list = request.json

    bloom_threshold = int(request.args.get('bloom', '1'))
    token_threshold = float(request.args.get('token', '0.8'))
    syntax_threshold = float(request.args.get('syntax', '0.8'))

    start_time = time.time()
    malicious_dict = main.detect(target_list, token_threshold, syntax_threshold, bloom_threshold)
    stop_time = time.time()

    malicious = []
    malicious_files = {}
    for idx, package in enumerate(malicious_dict.keys()):
        malicious.append(idx)
        malicious_files[idx] = list(malicious_dict[package].keys())

    return json.dumps({
        "run_time": stop_time - start_time,
        "malicious": malicious,
        "malicious_files": malicious_files
    })

@app.route("/detail", methods=['POST'])
def detail():
    target_list = request.json

    bloom_threshold = int(request.args.get('bloom', '1'))
    token_threshold = float(request.args.get('token', '0.8'))
    syntax_threshold = float(request.args.get('syntax', '0.8'))

    malicious_dict = main.detect(target_list, token_threshold, syntax_threshold, bloom_threshold)

    return json.dumps(malicious_dict)

if __name__ == '__main__':
    app.run("0.0.0.0", port=8000, debug=True)