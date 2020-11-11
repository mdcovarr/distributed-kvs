"""
    Implementation of shard node
"""

from flask import Flask, request, jsonify
import myconstants
import os

# Node's Key-Value store
kv_store = {}

app = Flask(__name__)

@app.route('/kvs/key-count', methods=['GET'])
def key_count():
    """
    Method used to handle getting key count of
    distributed key-value store
    :return count: the total count of keys in the store
    """
    return 'Hello, world!'

@app.route('/kvs/view-change', methods=['PUT'])
def view_change():
    """
    Method used to handle the changing of a view
    in the distributed key-value store
    :return status: the status of the HTTP PUT request
    """
    return 'Hello, world!'

@app.route('/kvs/keys/<string:key>', methods=['GET', 'PUT', 'DELETE'])
def keys(key):
    """
    Method used to handle the GET, PUT, or DELETE of a key
    in the distributed key-value store
    :param key: the key of interest
    :return status: the response of the given HTTP request
    """