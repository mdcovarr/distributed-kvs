"""
    Implementation of shard node
"""

from flask import Flask, request, jsonify
from uhashring import HashRing
import json
import requests
import myconstants
import os
import sys
import time

class ShardNodeWrapper(object):
    """
        Class object to wrapp around Flask server and
        needed variables e.g., key-value store
    """
    def __init__(self, ip, port, view, repl_factor):
        self.app = Flask(__name__)                  # The Flask Server (Node)
        self.kv_store = {}                          # The local key-value store
        self.view = view.split(',')                 # The view, IP and PORT address of other nodes
        self.ip = ip
        self.port = port
        self.address = ''
        self.repl_factor = repl_factor
        self.causal_context = {}


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
        self.app.add_url_rule(
                rule='/kvs/shards', endpoint='shards', view_func=self.shards, methods=['GET'])
        self.app.add_url_rule(
                rule='/kvs/shards/<string:shard_id>', endpoint='shard_id', view_func=self.handle_shard_id, methods=['GET'])

        """
            Proxy Routes
            /proxy/kvs/keys/<key>
        """
        self.app.add_url_rule(
                rule='/proxy/replicate/<string:key>', endpoint='replicate', view_func=self.replicate, methods=['PUT'])
        self.app.add_url_rule(
                rule='/proxy/kvs/keys/<string:key>', endpoint='proxy_keys', view_func=self.proxy_keys, methods=['GET', 'PUT', 'DELETE'])
        self.app.add_url_rule(
                rule='/proxy/view-change', endpoint='proxy_view_change', view_func=self.proxy_view_change, methods=['PUT'])
        # receive dictionary from other nodes
        self.app.add_url_rule(
                rule='/proxy/receive-dict', endpoint='proxy_receive_dict', view_func=self.proxy_receive_dict, methods=['PUT'])
        # used to trigger gossip
        self.app.add_url_rule(
                rule='/proxy/node-causal-context', endpoint='get_node_context', view_func=self.node_causal_context, methods=['GET', 'PUT'])


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
            pass

    def setup_pototetial_replicas(self):
        """
        Determine which nodes in the view should be this nodes replica
        This is done via the VIEW and REPL_FACTOR
        :return None:
        """
        replica_partitions = {}

        for i in range(len(self.view)):
            partition = (i % self.repl_factor) + 1
            partition_str = str(partition)

            try:
                replica_partitions[partition_str].append(self.view[i])
            except KeyError:
                replica_partitions[partition_str] = []
                replica_partitions[partition_str].append(self.view[i])

        # create dictionary for entire all shard_ids -> replicas
        self.all_partitions = replica_partitions

        # look for shard_id and replicas list for this node
        for key in replica_partitions:
            value = replica_partitions[key]
            if self.address in value:
                self.replicas = value
                self.shard_id = str(key)

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
        self.app.run(host=self.ip, port=self.port, debug=True)

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
        response['shard_id'] = self.shard_id
        code = 200

        return jsonify(response), code

    def shards(self):
        """
        Function used to get the list of shard id's in the current view
        """
        response = {}
        code = 200

        response['message'] = 'Shard membership retrieved successfully'

        shards = list(self.all_partitions.keys())
        shards.sort()
        response['shards'] = shards

        return jsonify(response), code

    def handle_shard_id(self, shard_id):
        """
        function used to handle the shard id REST API request
        """
        response = {}

        # 1. check if shard_id is our shard_id
        if shard_id == self.shard_id:
            response['message'] = 'Shard information retrieved successfully'
            response['shard_id'] = self.shard_id
            response['key-count'] = len(self.kv_store)
            response['replicas'] = self.replicas
            code = 200

            return jsonify(response), code

        # 2. get list of replicas pertaining to shard_id
        replicas = self.all_partitions[shard_id]

        # 3. Should query nodes in replicas list to get a response
        #    of their key-count
        for node_address in replicas:
            # send a /kvs/key-count request
            url = os.path.join('http://', node_address, 'kvs/key-count')

            try:
                resp = requests.get(url, timeout=myconstants.TIMEOUT)

                # if we get a response
                json_resp = json.loads(resp.text)
                key_count = json_resp['key-count']
                response['message'] = 'Shard information retrieved successfully'
                response['shard_id'] = shard_id
                response['key-count'] = key_count
                response['replicas'] = replicas
                code = 200

                return jsonify(response), code
            except:
                print('Error: cannot contact shard node')

        # TODO: Maybe handle the case that all nodes in shard_id are down?
        #       however, TA said this will not occur

    def view_change(self):
        """
        Method used to handle the changing of a view
        in the distributed key-value store
        :return status: the status of the HTTP PUT request
        """
        response = {}

        # Only accepting PUT requests
        try:
            contents = request.get_json()
        except:
            print('Error: Invalid json')

        try:
            new_view = contents['view']
        except:
            print('Error: unable to get new view key value from json')

        """
            0. We need to determine the replicas given a replication factor
        """
        repl_factor = int(contents['repl-factor'])
        partitions = {}
        view_list = list(new_view.split(','))

        for i in range(len(view_list)):
            shard_id = str((i % repl_factor) + 1)

            try:
                partitions[shard_id].append(view_list[i])
            except KeyError:
                partitions[shard_id] = []
                partitions[shard_id].append(view_list[i])

        # create dictionary for entire all shard_ids -> replicas
        self.all_partitions = partitions

        # look for shard_id and replicas list for this node
        for key in partitions:
            value = partitions[key]
            if self.address in value:
                self.replicas = value
                self.shard_id = str(key)

        shard_keys = list(self.all_partitions.keys())
        hr = HashRing(nodes=shard_keys)
        new_dict = {}

        # at this point we need to perform hashing
        # create id to shard_node replica dictionary

        """
            1. Tell all other nodes in old view to re hash keys
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
            2. Hash keys
        """
        for key in shard_keys:
            new_dict[str(key)] = {}

        for key in self.kv_store:
            new_address = hr.get_node(key)
            new_dict[new_address][key] = self.kv_store[key]

        """
            3. Update VIEW
        """
        self.view = view_list

        """
            4. Now need to determine which keys will stay
            on this current node
        """
        new_kv_store = {}

        for key in new_dict:
            if self.shard_id == key:
                new_kv_store = new_dict[key].copy()

        new_dict.pop(self.shard_id, None)
        self.kv_store = new_kv_store

        """
            5. Now need to send other nodes their new key values
        """
        for shard_id in new_dict:
            replicas = self.all_partitions[shard_id]

            for node_address in replicas:
                url = os.path.join('http://', node_address, 'proxy/receive-dict')
                payload = json.dumps(new_dict[shard_id])

                try:
                    resp = requests.put(url, json=payload, timeout=myconstants.TIMEOUT)
                except:
                    print('TODO: better error handling sending dictionary to another shard node')

        """
            6. Hopefully by this time we all nodes are done resharding so query for meta data
        """
        response['message'] = 'View change successful'
        response['shards'] = []
        code = 200

        for shard_id in self.all_partitions:
            node_data = {}

            if shard_id == self.shard_id:
                node_data['shard-id'] = shard_id
                node_data['key-count'] = len(self.kv_store)
                node_data['replicas'] = self.all_partitions[shard_id]
            else:
                for node_address in self.all_partitions[shard_id]:
                    url = os.path.join('http://', node_address, 'kvs/key-count')

                    try:
                        resp = requests.get(url, timeout=myconstants.TIMEOUT)

                        json_resp = json.loads(resp.text)
                        node_data['shard-id'] = shard_id
                        node_data['key-count'] = json_resp['key-count']
                        node_data['replicas'] = self.all_partitions[shard_id]
                        break
                    except (requests.Timeout, requests.exceptions.ConnectionError):
                        print('Not able to get key count of annother shard')

            response['shards'].append(node_data)

        """
            7. Reset causal context
        """
        self.causal_context = {}

        return jsonify(response), code

    def proxy_view_change(self):
        """
        Method to handle receiving a proxy view change. If a node
        receives a proxy view change, it means that another node was the
        node who received the initial /view-change from the client
        """
        response = {}
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

        repl_factor = int(contents['repl-factor'])
        partitions = {}
        view_list = list(new_view.split(','))

        for i in range(len(view_list)):
            shard_id = str((i % repl_factor) + 1)

            try:
                partitions[shard_id].append(view_list[i])
            except KeyError:
                partitions[shard_id] = []
                partitions[shard_id].append(view_list[i])

        # create dictionary for entire all shard_ids -> replicas
        self.all_partitions = partitions

        # look for shard_id and replicas list for this node
        for key in partitions:
            value = partitions[key]
            if self.address in value:
                self.replicas = value
                self.shard_id = str(key)

        # at this point we need to perform hashing
        # create id to shard_node dictionary
        shard_keys = list(self.all_partitions.keys())
        hr = HashRing(nodes=shard_keys)
        new_dict = {}

        """
            1. Update VIEW
        """
        self.view = view_list

        """
            2. Hash keys
        """
        for key in shard_keys:
            new_dict[str(key)] = {}

        for key in self.kv_store:
            new_address = hr.get_node(key)
            new_dict[new_address][key] = self.kv_store[key]

        """
            3. Now need to determine which keys will stay
            on this current node
        """
        new_kv_store = {}

        for key in new_dict:
            if self.shard_id == key:
                new_kv_store = new_dict[key].copy()

        new_dict.pop(self.shard_id, None)
        self.kv_store = new_kv_store

        """
            4. Now need to send other nodes their new key values
        """
        for shard_id in new_dict:
            replicas = self.all_partitions[shard_id]

            for node_address in replicas:
                url = os.path.join('http://', node_address, 'proxy/receive-dict')
                payload = json.dumps(new_dict[shard_id])

                try:
                    resp = requests.put(url, json=payload, timeout=myconstants.TIMEOUT)
                except:
                    print('TODO: better error handling sending dictionary to another shard node')

        """
            5. Reset causal context
        """
        self.causal_context = {}

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
            contents = json.loads(request.get_json())
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
        contents = request.get_json()
        context = contents['causal-context']
        resp = None

        """
            GET requests handling
        """
        if request.method == 'GET':
            if key in self.kv_store:
                response['doesExist'] = True
                response['message'] = myconstants.RETRIEVED_MESSAGE
                response['value'] = self.kv_store[key]
                response['causal-context'] = context
                code = 200

                return jsonify(response), code
            else:
                """
                    Need to ask other nodes of each shard
                    NOTE: need to make sure we communicate with at least
                          one node for each shard
                """
                proxy_path = 'proxy/kvs/keys'

                for shard_id in self.all_partitions:
                    # don't execute loop if shard_id is of this node
                    if shard_id == self.shard_id:
                        continue

                    partition = self.all_partitions[shard_id]

                    for node_address in partition:
                        url = os.path.join('http://', node_address, proxy_path, key)

                        try:
                            resp = requests.get(url, json=contents, timeout=myconstants.TIMEOUT)
                            resp_dict = json.loads(resp.text)

                            if resp_dict['doesExist'] == True:
                                """
                                    We found the key on another Shard Node
                                    now forward response back to client
                                """
                                return resp.text, resp.status_code
                            else:
                                """
                                    We were able to contact a node for a given shard
                                    so no need to contact other nodes for the same shard
                                    replica. Thus we can break from loop
                                """
                                break
                        except (requests.Timeout, requests.exceptions.ConnectionError):
                            """
                                We were not able to connect to another node, maybe node is
                                down? Thus continue to try and contact other nodes for a
                                certain shard
                            """
                            continue

            # At this point we did not find a shard with the given key,
            # so just return the response from the last node we contacted
            return resp.text, resp.status_code

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

            if key in self.kv_store:
                try:
                    self.kv_store[key] = contents['value']
                except:
                    # Error: Key value did not exist
                    response['message'] = 'Error in PUT'
                    response['error'] = 'Value is missing'
                    response['causal-context'] = context
                    response['address'] = self.address
                    code = 400
                    return jsonify(response), code


                message = myconstants.UPDATED_MESSAGE
                code = 200

                """
                    Replicate

                    Need to tell all other nodes in same replica about the
                    newly inserted/update value
                """
                for node_address in self.all_partitions[self.shard_id]:
                    if node_address == self.address:
                        continue

                    url = os.path.join('http://', node_address, 'proxy/replicate', key)

                    try:
                        resp = requests.put(url, json=request.get_json(), timeout=myconstants.TIMEOUT)

                    except (requests.Timeout, requests.exceptions.ConnectionError):
                        print('we were not able to communicate with another replica')


                response['replaced'] = True
                response['message'] = message
                response['causal-context'] = context

                return jsonify(response), code
            else:
                proxy_path = 'proxy/kvs/keys'

                for shard_id in self.all_partitions:
                    if shard_id == self.shard_id:
                        continue

                    for node_address in self.all_partitions[shard_id]:
                        url = os.path.join('http://', node_address, proxy_path, key)

                        try:
                            resp = requests.get(url, json=content, timeout=myconstants.TIMEOUT)
                            resp_dict = json.loads(resp.text)

                            if resp_dict['doesExist'] == True:
                                """
                                    We found the key on another shard node
                                    Now need to update key on the determined node
                                """
                                resp = requests.put(url, json=contents, timeout=myconstants.TIMEOUT)
                                return resp.text, resp.status_code
                            else:
                                """
                                    We didn't find the key in this shard, so no need to talk to
                                    other replicas of same shard
                                """
                                break
                        except (requests.Timeout, requests.exceptions.ConnectionError):
                            continue


                # At this point none of the shards have the given key
                # Will have to get the key_count from all the nodes to balance the insertion.
                min_key_count = len(self.kv_store)
                min_node_address = self.address

                path = 'kvs/key-count'

                for shard_id in self.all_partitions:
                    if shard_id == self.shard_id:
                        continue

                    for node_address in self.all_partitions[shard_id]:
                        url = os.path.join('http://', node_address, path)

                        try:
                            resp = requests.get(url, timeout=myconstants.TIMEOUT)
                            resp_dict = json.loads(resp.text)

                            if min_key_count > resp_dict['key-count']:
                                min_key_count = resp_dict['key-count']
                                min_node_address = node_address

                            # we have talked to a node with the given shard thus we can
                            # move on to a new shard
                            break
                        except (requests.Timeout, requests.exceptions.ConnectionError):
                            continue


                if min_node_address == self.address:
                    try:
                        value = content['value']
                    except:
                        # Error: Key value did not exist
                        response['message'] = 'Error in PUT'
                        response['error'] = 'Value is missing'
                        response['causal-context'] = context
                        code = 400
                        return jsonify(response), code

                    if len(key) > myconstants.KEY_LENGTH:
                        response['message'] = 'Error in PUT'
                        response['error'] = 'Key is too long'
                        response['causal-context'] = context
                        code = 400
                        return jsonify(response), code

                    self.kv_store[key] = value

                    """
                        Replicate

                        Need to tell all other nodes in same replica about the
                        newly inserted/update value
                    """
                    for node_address in self.all_partitions[self.shard_id]:
                        if node_address == self.address:
                            continue

                        url = os.path.join('http://', node_address, 'proxy/replicate', key)

                        try:
                            resp = requests.put(url, json=request.get_json(), timeout=myconstants.TIMEOUT)

                        except (requests.Timeout, requests.exceptions.ConnectionError):
                            print('we were not able to communicate with another replica')

                    response['replaced'] = False
                    response['message'] = myconstants.ADDED_MESSAGE
                    response['causal-context'] = context
                    code = 201

                    return jsonify(response), code
                else:
                    try:
                        proxy_path = 'proxy/kvs/keys'

                        url = os.path.join('http://', min_node_address, proxy_path, key)

                        resp = requests.put(url, json=content, timeout=myconstants.TIMEOUT)

                        return resp.text, resp.status_code

                    except (requests.Timeout, requests.exceptions.ConnectionError):
                        # Shard Node we are forwarding to was down
                        error = 'Main instance is down'
                        message = 'Error in PUT'
                        status_code = 503
                        res_dict = {'error': error, 'message': message}

                        return jsonify(res_dict), status_code

        """
            DELETE requests handling
        """
        if request.method == 'DELETE':
            if key in self.kv_store:
                # Need to delete key value from store
                del self.kv_store[key]

                response['doesExist'] = True
                response['message'] = myconstants.DELETE_SUCCESS_MESSAGE

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
        contents = request.get_json()
        context = contents['causal-context']
        code = 999

        """
            GET requests handling forward from another shard node
        """
        if request.method == 'GET':
            if key in self.kv_store:
                response['doesExist'] = True
                response['message'] = myconstants.RETRIEVED_MESSAGE
                response['value'] = self.kv_store[key]
                response['address'] = self.address
                response['causal-context'] = context
                code = 200
            else:
                response['doesExist'] = False
                response['error'] = myconstants.KEY_ERROR
                response['message'] = myconstants.GET_ERROR_MESSAGE
                response['address'] = self.address
                response['causal-context'] = context
                code = 404

            return jsonify(response), code

        """
            PUT requests handling forward from another shard node
        """
        if request.method == 'PUT':
            contents = request.get_json()
            context = contents['causal-context']

            try:
                value = contents['value']
            except:
                # Error: Key value did not exist
                response['message'] = 'Error in PUT'
                response['error'] = 'Value is missing'
                response['causal-context'] = context
                response['address'] = self.address
                code = 400
                return jsonify(response), code

            if len(key) > myconstants.KEY_LENGTH:
                response['message'] = 'Error in PUT'
                response['error'] = 'Key is too long'
                response['causal-context'] = context
                response['address'] = self.address
                code = 400
                return jsonify(response), code


            # at this point we have a valid value and key
            if key in self.kv_store:
                replaced = True
                message = myconstants.UPDATED_MESSAGE
                code = 200
            else:
                replaced = False
                message = myconstants.ADDED_MESSAGE
                code = 201

            """
                Replicate

                Need to tell all other nodes in same replica about the
                newly inserted/update value
            """
            for node_address in self.all_partitions[self.shard_id]:
                if node_address == self.address:
                    continue

                url = os.path.join('http://', node_address, 'proxy/replicate', key)

                try:
                    resp = requests.put(url, json=request.get_json(), timeout=myconstants.TIMEOUT)

                except (requests.Timeout, requests.exceptions.ConnectionError):
                    print('we were not able to communicate with another replica')

            # Respond back to client
            response['replaced'] = replaced
            response['message'] = message
            response['causal-context'] = context
            response['address'] = self.address

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

    def replicate(self, key):
        """
        Function used to handle other nodes reveiving a replicated value from
        another node in the same replica
        """
        response = {}
        code = 999
        contents = request.get_json()
        context = contents['causal-context']
        value = contents['value']

        # at this point we have a valid value and key
        if key in self.kv_store:
            replaced = True
            message = myconstants.UPDATED_MESSAGE
            code = 200
        else:
            replaced = False
            message = myconstants.ADDED_MESSAGE
            code = 201

        response['replaced'] = replaced
        response['message'] = message
        response['causal-context'] = context
        response['address'] = self.address

        self.kv_store[key] = value

        return jsonify(response), code

    def handle_causal_context(self, key, value):
        """
        Function used to handle the addition of an event to
        the current causal context
        :param key: key in API call (e.g. http://127.0.0.1:13800/kvs/keys/<key>)
        """
        curr_time = time.time()

        # Add event to causal context
        try:
            self.causal_context[key][str(curr_time)] = value
        except:
            print('Error: Issue adding to causal context')

    def handle_gossip(self):
        """
        Function used to get the causal context of other replica nodes in
        same shard
        :return None:
        """
        # need to check if node is 1st node on list of replicas
        if self.address != self.replicas[0]:
            return

        """
            1. At this point the current node we are on is 1st in replicas list,
               and thus should trigger gossip
        """
        all_context = self.causal_context


        for node_address in self.replicas:
            # We don't need to contact ourselves
            if self.address == node_address:
                continue

            url = os.path.join('http://', node_address, 'proxy/node-causal-context')

            try:
                resp = requests.get(url, timeout=myconstants.TIMEOUT)

            except (requests.Timeout, requests.exceptions.ConnectionError):
                """
                    We were not able to contact one of our replicas thus
                    we should just stop process of gossiping
                """
                print('we were not able to communicate with another replica')
                return

            # Need to extract node's causal context
            resp_dict = json.loads(resp.text)
            node_context = resp_dict['causal-context']

            """
                2. Combine current causal context, with incoming causal context of node
            """
            new_context = {**all_context, **node_context}

            for key, value in new_context.items():
                # Check if key exists in both nodes
                if key in all_context and key in node_context:
                    # Check timestamp if both nodes have a certain key value
                    if float(node_context[key]['timestamp']) > float(value['timestamp']):
                        new_context[key] = node_context[key]['timestamp']

            all_context = new_context


            """
                3. At this point we have determined the causal context for all the replicas.
                   Need to distributed to replicas and update our own causal context
            """
            for node_address in self.replicas:
                if self.address == node_address:
                    continue

                url = os.path.join('http://', node_address, 'proxy/node-causal-context')

                try:
                    resp = requests.put(url, json=json.dumps(all_context), timeout=myconstants.TIMEOUT)
                except (requests.Timeout, requests.exceptions.ConnectionError):
                    print('Error: Was not able to reach node when updating causal context')

            """
                4. Current Node needs to update it's kv-store and context, based off all_context
            """
            self.causal_context = all_context

            for key, value in self.causal_context:
                self.kv_store[key] = value['value']

    def node_causal_context(self):
        """
        Function used to handle GET and PUT requests of Causal Context
        :return None:
        """
        response = {}
        code = 200

        if request.method == 'GET':
            response['causal-context'] = self.causal_context

            return jsonify(response), code

        if request.method == 'PUT':
            try:
                contents = request.get_json()
            except:
                print('Error: Invalid json')

            self.causal_context = contents

            for key, value in self.causal_context:
                self.kv_store[key] = value['value']

            return jsonify(response), code