from flask import Flask
from flask import request
from flask import jsonify
from flask import Response
import requests
import os

FORWARDING_ADDRESS = '127.0.0.1:13800' #os.environ.get('FORWARDING_ADDRESS')
TIMEOUT = 6

app = Flask(__name__)

@app.route('/<path:path>', methods=['GET', 'PUT', 'DELETE'])
def kvs_proxy(path):
    response = {}
    url = os.path.join('http://', FORWARDING_ADDRESS, path)

    if request.method == 'GET':
        try:
            resp = requests.get(url, timeout=TIMEOUT)
        except Exception as e:
            response['error'] = 'Main instance is down'
            response['message'] = 'Error in GET'
            return jsonify(response), 503
        return resp.text, resp.status_code

    if request.method == 'PUT':
        try:
            resp = requests.put(url, json=request.get_json(), timeout=TIMEOUT)
        except Exception as e:
            response['error'] = 'Main instance is down'
            response['message'] = 'Error in PUT'
            return jsonify(response), 503
        return resp.text, resp.status_code

    if request.method == 'DELETE':
        try:
            resp = requests.delete(url, timeout=TIMEOUT)
        except Exception as e:
            response['error'] = 'Main instance is down'
            response['message'] = 'Error in DELETE'
            return jsonify(response), 503
        return resp.text, resp.status_code

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=13801)
