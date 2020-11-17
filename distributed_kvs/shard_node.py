"""
    Implementation of shard node
"""

from flask import Flask, request, jsonify
import json
import requests
import myconstants
import os

app = Flask(__name__)
class ShardNodeWrapper(object):
    """
        Class object to wrapp around Flask server and
        needed variables e.g., key-value store
    """
    def __init__(self, ip, port):
        self.app = Flask(__name__)                  # The Flask Server (Node)
        self.kv_store = {}                          # The local key-value store
        self.view = []                              # The view, IP and PORT address of other nodes
        self.ip = ip
        self.port = port
        self.address = str(self.ip) + ':' + str(self.port)    # IP and PORT address of the current node

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
                rule='/proxy/kvs/keys/<string:key>', endpoint='proxy_keys', view_func=self.proxy_keys, methods=['GET', 'PUT', 'DELETE'])

    def setup_view(self):
        """
        Method to setup the view of the current node
        :return None:
        """
        view_string = '127.0.0.1:13801' #os.environ.get('VIEW')
        self.view = view_string.split(',')

    def run(self):
        """
        Method to start flask server
        :return None:
        """
        self.app.run(host=self.ip, port=self.port)

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

        # TODO: 
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
                """
                    Need to ask other nodes if they have the key
                """
                proxy_path = 'proxy/kvs/keys'

                for node_address in self.view:
                    url = os.path.join('http://', node_address, proxy_path, key)

                    try:
                        resp = requests.get(url, timeout=myconstants.TIMEOUT)
                        resp_dict = json.loads(resp.text)

                        if resp_dict['doesExist'] == True:
                            """
                                We found the key on another Shard Node
                                now forward response back to client
                            """
                            return resp.text, resp.status_code

                    except (requests.Timeout, requests.exceptions.ConnectionError):
                        # Shard Node we are forwarding to was down

                        error = 'Main instance is down'
                        message = 'Error in PUT'
                        status_code = 503
                        res_dict = {'error': error, 'message': message}

                        return jsonify(res_dict), status_code


                response['doesExist'] = False
                response['error'] = myconstants.KEY_ERROR
                response['message'] = myconstants.GET_ERROR_MESSAGE
                code = 404

            return jsonify(response), code


        """
            PUT requests handling
        """
        if request.method == 'PUT':
            """
                1. Need to determine if PUT request is an 'update' or 'insert'

                An 'update' is determined if current shard node or any other shard node
                has the existing key

                A 'insert' is determined if no shard node has the current key.
                Also will want to insert key to node with least amount of keys
            """
            try:
                content = request.get_json()
            except:
                # Error: Invalid Json format
                return jsonify(myconstants.BAD_FORMAT_RESPONSE), 400


        """
            DELETE requests handling
        """
        if request.method == 'DELETE':
            if key in self.kv_store:
                # Need to delete key value from store
                del self.kv_store[key]

                response['doesExist'] = True
                response['message'] = myconstants.DELETE_SUCCESS_MESSAGE
                response['address'] = self.address
                code = 200
            else:
                """
                    Need to ask other nodes if they have the key
                """
                proxy_path = 'proxy/kvs/keys'

                for node_address in self.view:
                    url = os.path.join('http://', node_address, proxy_path, key)

                    try:
                        resp = requests.delete(url, timeout=myconstants.TIMEOUT)
                        resp_dict = json.loads(resp.text)

                        if resp_dict['doesExist'] == True:
                            """
                                We found the key on another Shard Node
                                now forward response back to client
                            """
                            return resp.text, resp.status_code


                    except (requests.Timeout, requests.exceptions.ConnectionError):
                        # Shard Node we are forwarding to was down

                        error = 'Main instance is down'
                        message = 'Error in PUT'
                        status_code = 503
                        res_dict = {'error': error, 'message': message}

                        return jsonify(res_dict), status_code

                response['doesExist'] = False
                response['error'] = myconstants.KEY_ERROR
                response['message'] = myconstants.DELETE_ERROR_MESSAGE
                code = 404

            return jsonify(response), code


    def proxy_keys(self, key):
        """
        Method similar to keys, but instead it does not ask other nodes about a key.
        proxy_keys just returns whether it finds its key in it's local storage or not
        """
        response = {}

        """
            GET requests handling forward from another shard node
        """
        if request.method == 'GET':
            if key in self.kv_store:
                response['doesExist'] = True
                response['message'] = myconstants.RETRIEVED_MESSAGE
                response['value'] = self.kv_store[key]
                response['address'] = self.address
                code = 200
            else:
                response['doesExist'] = False
                response['error'] = myconstants.KEY_ERROR
                response['message'] = myconstants.GET_ERROR_MESSAGE
                code = 404

            return jsonify(response), code

        """
            PUT requests handling forward from another shard node
        """
        if request.method == 'PUT':
            try:
                content = request.get_json()
            except:
                # Error: Invalid Json format
                return jsonify(myconstants.BAD_FORMAT_RESPONSE), 400

            try:
                value = content['value']
            except:
                # Error: Key value did not exist
                return jsonify(myconstants.MISSING_RESPONSE), 400

            if len(key) > myconstants.KEY_LENGTH:
                return jsonify(myconstants.LONG_KEY_RESPONSE), 400

            # at this point we have a valid value and key
            if key in self.kv_store:
                replaced = True
                message = myconstants.UPDATED_MESSAGE
                code = 200
            else:
                replaced = False
                message = myconstants.ADDED_MESSAGE
                response['address'] = self.address
                code = 201

            response['replaced'] = replaced
            response['message'] = message

            self.kv_store[key] = value

            return jsonify(response), code

        """
            DELETE requests handling forward from another shard node
        """
        if request.method == 'DELETE':
            if key in self.kv_store:
                # Need to delete key value from store
                del self.kv_store[key]

                response['doesExist'] = True
                response['message'] = myconstants.DELETE_SUCCESS_MESSAGE
                response['address'] = self.address
                code = 200
            else:
                response['doesExist'] = False
                response['error'] = myconstants.KEY_ERROR
                response['message'] = myconstants.DELETE_ERROR_MESSAGE
                code = 404

            return jsonify(response), code
