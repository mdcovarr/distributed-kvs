"""
    Implementation of shard node
"""

from flask import Flask, request, jsonify
import myconstants
import os

app = Flask(__name__)
class ShardNodeWrapper(object):
    """
        Class object to wrapp around Flask server and
        needed variables e.g., key-value store
    """
    def __init__(self):
        self.app = Flask(__name__)                  # The Flask Server (Node)
        self.kv_store = {'sampleKey': 'sampleValue'}                          # The local key-value store
        self.view = []                              # The view, IP and PORT address of other nodes
        self.address = '' #os.environ.get('ADDRESS')    # IP and PORT address of the current node

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

        """
            Proxy Routes
            /proxy/kvs/keys/<key>
        """
        self.app.add_url_rule(
                rule='/proxy/kvs/<string:key>', endpoint='proxy_keys', view_func=self.proxy_keys, methods=['GET', 'PUT', 'DELETE'])

    def setup_view(self):
        """
        Method to setup the view of the current node
        :return None:
        """
        view_string = '' #os.environ.get('VIEW')
        self.view = view_string.split(',')

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
        response = {}
        count = len(self.kv_store)

        response['message'] = 'Key count retrieved successfully'
        response['key-count'] = count
        code = 200

        return jsonify(response), code


    def view_change(self):
        """
        Method used to handle the changing of a view
        in the distributed key-value store
        :return status: the status of the HTTP PUT request
        """
        response = {}
        contents = request.get_json()

        # need to update view
        # need to tell other nodes to update their view
        # perform repartitioning of the keys

        response['message'] = 'View change successful'
        response['shards'] = []
        code = 200

        return jsonify(response), code

    def keys(self, key):
        """
        Method used to handle the GET, PUT, or DELETE of a key
        in the distributed key-value store
        :param key: the key of interest
        :return status: the response of the given HTTP request
        """
        response = {}

        """
            GET requests handling
        """
        if request.method == 'GET':
            if key in self.kv_store:
                response['doesExist'] = True
                response['message'] = myconstants.RETRIEVED_MESSAGE
                response['value'] = self.kv_store[key]
                code = 200
            else:
                # Need to ask all other nodes
                response['doesExist'] = False
                response['error'] = myconstants.KEY_ERROR
                response['message'] = myconstants.GET_ERROR_MESSAGE
                code = 404

        return jsonify(response), code



        """
            PUT requests handling
        """
        if request.method == 'PUT':
            print('handing PUT')

        """
            DELETE requests handling
        """
        if request.method == 'DELETE':
            print('handing DELETE')

    def proxy_keys(self, key):
        """
        Method similar to keys, but instead it does not ask other nodes about a key.
        proxy_keys just returns whether it finds its key in it's local storage or not
        """

        """
            GET requests handling
        """
        if request.method == 'GET':
            print('handing GET')

        """
            PUT requests handling
        """
        if request.method == 'PUT':
            print('handing PUT')

        """
            DELETE requests handling
        """
        if request.method == 'DELETE':
            print('handing DELETE')
