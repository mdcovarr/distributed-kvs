"""
    Implementation of shard node
"""

from flask import Flask, request, jsonify
import myconstants
import os

# Node's Key-Value store
kv_store = {}

app = Flask(__name__)
class ShardNodeWrapper(object):
    """
        Class object to wrapp around Flask server and
        needed variables e.g., key-value store
    """
    def __init__(self):
        self.app = Flask(__name__)
        self.kv_store = {}
        self.views = {}
        self.address = ''

    def setup_routes(self):
        """
        Method used to set up the url rules for the Flask app
            /kvs/keys/<key>
            /kvs/key-count
            /kvs/view-change
        :return None:
        """
        self.app.add_url_rule(
                rule='/kvs/key-count', endpoint='key_count', view_func=self.key_count, methods=['GET'])
        self.app.add_url_rule(
                rule='/kvs/view-change', endpoint='view_change', view_func=self.view_change, methods=['PUT'])
        self.app.add_url_rule(
                rule='/kvs/keys/<string:key>', endpoint='keys', view_func=self.keys, methods=['GET', 'PUT', 'DELETE'])

    def run(self):
        """
        Method to start flask server
        :return None:
        """
        self.app.run(host='127.0.0.1', port=13800)

    def key_count(self):
        """
        Method used to handle getting key count of
        distributed key-value store
        :return count: the total count of keys in the store
        """
        return 'Hello, world!'

    def view_change(self):
        """
        Method used to handle the changing of a view
        in the distributed key-value store
        :return status: the status of the HTTP PUT request
        """
        return 'Hello, world!'

    def keys(self, key):
        """
        Method used to handle the GET, PUT, or DELETE of a key
        in the distributed key-value store
        :param key: the key of interest
        :return status: the response of the given HTTP request
        """
        return 'Hello, world!'