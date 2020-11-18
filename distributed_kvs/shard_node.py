"""
    Implementation of shard node
"""

from flask import Flask, request, jsonify
from uhashring import HashRing
import json
import requests
import myconstants
import os

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

        """
            Proxy Routes
            /proxy/kvs/keys/<key>
        """
        self.app.add_url_rule(
                rule='/proxy/kvs/keys/<string:key>', endpoint='proxy_keys', view_func=self.proxy_keys, methods=['GET', 'PUT', 'DELETE'])
        self.app.add_url_rule(
                rule='/proxy/kvs/keys/<string:key>', endpoint='proxy_keys', view_func=self.proxy_keys, methods=['GET', 'PUT', 'DELETE'])
        self.app.add_url_rule(
                rule='/proxy/kvs/view-change', endpoint='proxy_view_change', view_func=self.proxy_view_change, methods=['PUT'])
        # receive dictionary from other nodes
        self.app.add_url_rule(
                rule='/proxy/receive-dict', endpoint='proxy_receive_dict', view_func=self.proxy_receive_dict, methods=['PUT'])

    def setup_view(self):
        """
        Method to setup the view of the current node
        :return None:
        """
        view_string = os.environ.get('VIEW')

        try:
            # This is for deployment environment
            self.view = view_string.split(',')
        except AttributeError:
            # this is for development environment
            self.view = []

    def setup_address(self):
        """
        Method used to setup the address of the shard node. If os.environ.get('ADDRESS')
        is an empty string '', that means we are in development. If ADDRESS is NOT empty,
        that means we are in deployment docker
        :return None: No return from function
        """
        address = os.environ.get('ADDRESS')

        if address:
            self.address = address
        else:
            self.address = str(self.ip) + ':' + str(self.port)

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

        # TODO:
        # need to update view
        # need to tell other nodes to update their view
        # perform repartitioning of the keys

        # Only accepting PUT requests
        try:
            contents = request.get_json()
        except:
            print('Error: Invalid json')

        try:
            new_view = contents['view']
        except:
            print('Error: unable to get new view key value from json')

        # at this point we need to perform hashing
        # create id to shard_node dictionary
        view_list = list(new_view.split(','))
        hr = HashRing(nodes=view_list)
        new_dict = {}

        """
            1. Update VIEW
        """
        self.view = view_list

        """
            2. Hash keys
        """
        for key in view_list:
            new_dict[key] = {}

        for key in self.kv_store:
            new_address = hr.get_node(key)
            new_dict[new_address][key] = self.kv_store[key]

        """
            3. Tell all other nodes in old view to re hash keys
        """
        for node_address in self.view:
            # do not execute loop if node_address is our own address
            if node_address == self.address:
                continue

            url = os.path.join('http://', node_address, 'proxy/view-change')

            try:
                resp = requests.put(url, json=request.get_json(), timeout=myconstants.TIMEOUT)
            except:
                print('Error: cannot notify shard node of view change')

        """
            4. Now need to determine which keys will stay
            on this current node
        """
        new_kv_store = {}

        for key in new_dict:
            if key == self.address:
                new_kv_store = new_dict[key].copy()

        new_dict.pop(self.address, None)

        """
            5. Now need to send other nodes their new key values
        """
        for node_address in new_dict:
            url = os.path.join('http://', node_address, 'proxy/receive-dict')
            payload = new_dict[node_address]

            try:
                resp = requests.put(url, json=json.dumps(payload), timeout=myconstants.TIMEOUT)
            except:
                print('TODO: better error handling sending dictionary to another shard node')


        # TODO correct response -------------

        response['message'] = 'View change successful'
        response['shards'] = []
        code = 200

        return jsonify(response), code

    def proxy_view_change(self):
        """
        Method to handle receiving a proxy view change. If a node
        receives a proxy view change, it means that another node was the
        node who received the initial /view-change from the client
        """
        response = {}
        response['message'] = 'View change successful'
        code = 200

        # Only accepting PUT requests
        try:
            contents = request.get_json()
        except:
            print('Error: Invalid json')

        try:
            new_view = contents['view']
        except:
            print('Error: unable to get new view key value from json')

        # at this point we need to perform hashing
        # create id to shard_node dictionary
        view_list = list(new_view.split(','))
        hr = HashRing(nodes=view_list)
        new_dict = {}

        """
            1. Update VIEW
        """
        self.view = view_list

        """
            2. Hash keys
        """
        for key in view_list:
            new_dict[key] = {}

        for key in self.kv_store:
            new_address = hr.get_node(key)
            new_dict[new_address][key] = self.kv_store[key]

        """
            3. Now need to determine which keys will stay
            on this current node
        """
        new_kv_store = {}

        for key in new_dict:
            if key == self.address:
                new_kv_store = new_dict[key].copy()

        new_dict.pop(self.address, None)

        """
            4. Now need to send other nodes their new key values
        """
        for node_address in new_dict:
            url = os.path.join('http://', node_address, 'proxy/receive-dict')
            payload = new_dict[node_address]

            try:
                resp = requests.put(url, json=json.dumps(payload), timeout=myconstants.TIMEOUT)
            except:
                print('TODO: better error handling sending dictionary to another shard node')

        return jsonify(response), code

    def proxy_receive_dict(self):
        """
        Function used to handle the receiving of a json kv store
        from another shard node
        """
        # only accepts PUT requests
        response = {}
        response['message'] = myconstants.UPDATED_MESSAGE
        code = 200

        try:
            contents = request.get_json()
        except:
            print('Error: Invalid Json')

        # Just need to add new keys to store
        self.kv_store = {**self.kv_store, **contents}

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
                    # don't execute loop if node_address is address of current shard node
                    if node_address == self.address:
                        continue

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

            try:
                value = content['value']
            except:
                # Error: Key value did not exist
                return jsonify(myconstants.MISSING_RESPONSE), 400

            if len(key) > myconstants.KEY_LENGTH:
                return jsonify(myconstants.LONG_KEY_RESPONSE), 400


            if key in self.kv_store:
                self.kv_store[key] = content['value']
                message = myconstants.UPDATED_MESSAGE
                code = 200

                response['replaced'] = True
                response['message'] = message
            else:

                proxy_path = 'proxy/kvs/keys'

                for node_address in self.view:
                    # don't execute loop if node_address is address of current shard node
                    if node_address == self.address:
                        continue

                    url = os.path.join('http://', node_address, proxy_path, key)

                    try:
                        resp = requests.get(url, timeout=myconstants.TIMEOUT)
                        resp_dict = json.loads(resp.text)

                        if resp_dict['doesExist'] == True:
                            """
                                We found the key on another Shard Node
                                now forward response back to client
                            """
                            resp = requests.put(url, timeout=myconstants.TIMEOUT)

                            return resp.text, resp.status_code

                    except (requests.Timeout, requests.exceptions.ConnectionError):
                        # Shard Node we are forwarding to was down
                        error = 'Main instance is down'
                        message = 'Error in PUT'
                        status_code = 503
                        res_dict = {'error': error, 'message': message}

                        return jsonify(res_dict), status_code

                # Not present in any of the other nodes
                self.kv_store[key] = content['value']
                response['replaced'] = False
                response['message'] = myconstants.ADDED_MESSAGE
                code = 201

            return jsonify(response), code

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
                    # don't execute loop if node_address is address of current shard node
                    if node_address == self.address:
                        continue

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

            # We will have a valid value and key as the validation is done in the main node
            content = request.get_json()
            self.kv_store[key] = content['value']
            message = myconstants.UPDATED_MESSAGE
            code = 200

            response['replaced'] = True
            response['message'] = message
            response['address'] = self.address

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
