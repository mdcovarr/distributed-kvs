from flask import Blueprint
from flask import Flask
from flask import request
from flask import jsonify
from flask import Response
import requests
import os
import myconstants

FORWARDING_ADDRESS = os.environ.get('FORWARDING_ADDRESS')

proxy_blueprint = Blueprint('proxy_blueprint', __name__)

@proxy_blueprint.route('/<path:path>', methods=['GET', 'PUT', 'DELETE'])
def kvs_proxy(path):
    response = {}
    url = os.path.join('http://', FORWARDING_ADDRESS, path)

    if request.method == 'GET':
        try:
            resp = requests.get(url, timeout=myconstants.TIMEOUT)
        except Exception as e:
            response['error'] = 'Main instance is down'
            response['message'] = 'Error in GET'
            return jsonify(response), 503
        return resp.text, resp.status_code

    if request.method == 'PUT':
        try:
            resp = requests.put(url, json=request.get_json(), timeout=myconstants.TIMEOUT)
        except Exception as e:
            response['error'] = 'Main instance is down'
            response['message'] = 'Error in PUT'
            return jsonify(response), 503
        return resp.text, resp.status_code

    if request.method == 'DELETE':
        try:
            resp = requests.delete(url, timeout=myconstants.TIMEOUT)
        except Exception as e:
            response['error'] = 'Main instance is down'
            response['message'] = 'Error in DELETE'
            return jsonify(response), 503
        return resp.text, resp.status_code
