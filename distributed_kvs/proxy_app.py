"""
    Flask Blueprint for the 'follower' or 'proxy' node.

    This file defines api route handler for follower not in order to
    redirect requests to the main node
"""

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
    """
    Method used to route GET, PUT and DELETE requests to the main node
    :param path: path after address and port of HTTP request e.g. http://127.0.0.1:13800/kvs/sampleKey
    :return: response from main node, and status code from main node
    """
    response = {}
    url = os.path.join('http://', FORWARDING_ADDRESS, path)

    """
        GET request handle
    """
    if request.method == 'GET':
        try:
            resp = requests.get(url, timeout=myconstants.TIMEOUT)
        except Exception as e:
            response['error'] = 'Main instance is down'
            response['message'] = 'Error in GET'
            return jsonify(response), 503
        return resp.text, resp.status_code

    """
        PUT request handle
    """
    if request.method == 'PUT':
        try:
            resp = requests.put(url, json=request.get_json(), timeout=myconstants.TIMEOUT)
        except Exception as e:
            response['error'] = 'Main instance is down'
            response['message'] = 'Error in PUT'
            return jsonify(response), 503
        return resp.text, resp.status_code

    """
        DELETE request handle
    """
    if request.method == 'DELETE':
        try:
            resp = requests.delete(url, timeout=myconstants.TIMEOUT)
        except Exception as e:
            response['error'] = 'Main instance is down'
            response['message'] = 'Error in DELETE'
            return jsonify(response), 503
        return resp.text, resp.status_code
