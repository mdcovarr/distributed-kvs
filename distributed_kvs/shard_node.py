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
        self.currentHashRing = None


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
        replica_count = int(len(self.view) / self.repl_factor)
        count = 1

        for i in range(0, len(self.view), replica_count):
            replica_partitions[str(count)] = self.view[i : i + replica_count]
            count += 1

        # create dictionary for entire all shard_ids -> replicas
        self.all_partitions = replica_partitions

        # get list of shard_id's for current_hash_ring
        shards = list(self.all_partitions.keys())
        self.currentHashRing = HashRing(nodes=shards)

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
        response['shard-id'] = self.shard_id
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
            response['shard-id'] = self.shard_id
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
                response['shard-id'] = shard_id
                response['key-count'] = key_count
                response['replicas'] = replicas
                code = 200

                return jsonify(response), code
            except:
                print('Error: cannot contact shard node')

        # Maybe handle the case that all nodes in shard_id are down?
        # However, TA said this will not occur



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
        count = 1

        for i in range(0, len(view_list), repl_factor):
            partitions[str(count)] = view_list[i : i + repl_factor]
            count += 1

        # get shard_id's for current hash ring
        shards = list(partitions.keys())
        self.currentHashRing = HashRing(nodes=shards)

        # create dictionary for entire all shard_ids -> replicas
        self.all_partitions = partitions

        # look for shard_id and replicas list for this node
        for key in partitions:
            value = partitions[key]
            if self.address in value:
                self.replicas = value
                self.shard_id = str(key)

        # to hold all shard IDs (here keys = python dictionary keys, not kvs keys!)
        shard_keys = list(self.all_partitions.keys())

        # hr = HashRing(nodes=shard_keys)
        self.currentHashRing = HashRing(nodes=shard_keys)

        new_dict = {}

        # at this point we need to perform hashing
        # create id to shard_node replica dictionary

        """
            1. Tell all other nodes in old view to re hash keys
        """
        all_nodes = self.view
        all_nodes.extend(view_list)
        all_nodes = set(all_nodes)
        all_nodes = list(all_nodes)

        for node_address in all_nodes:
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
            new_shard = self.currentHashRing.get_node(key)
            new_dict[new_shard][key] = self.kv_store[key]

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

        #new_dict.pop(self.shard_id, None)
        self.kv_store = new_kv_store

        """
            5. Now need to send other nodes their new key values
            TODO: what about updating own replicas?
            NOTE: I think they would have determined which nodes to keep on their own
        """
        for shard_id in new_dict:
            replicas = self.all_partitions[shard_id]

            for node_address in replicas:
                if node_address == self.address:
                    continue

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
        count = 1

        for i in range(0, len(view_list), repl_factor):
            partitions[str(count)] = view_list[i : i + repl_factor]
            count += 1

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

        # hr = HashRing(nodes=shard_keys)
        self.currentHashRing = HashRing(nodes=shard_keys)

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
            new_shard = self.currentHashRing.get_node(key)
            new_dict[new_shard][key] = self.kv_store[key]

        """
            3. Now need to determine which keys will stay
            on this current node
        """
        new_kv_store = {}

        for key in new_dict:
            if self.shard_id == key:
                new_kv_store = new_dict[key].copy()

        #new_dict.pop(self.shard_id, None)
        self.kv_store = new_kv_store

        """
            4. Now need to send other nodes their new key values.
        """
        for shard_id in new_dict:
            replicas = self.all_partitions[shard_id]

            for node_address in replicas:
                if node_address == self.address:
                    continue

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
        # context = contents['causal-context']

        resp = None

        message = None
        code = -1
        replaced = False

        """
            GET requests handling
        """
        if request.method == 'GET':

            # get shard of key
            correct_shard_id = self.currentHashRing.get_node(key)

            if correct_shard_id == self.shard_id:
                """
                    At this point key has been hashed to current node.
                    We still need to determine if key exists
                """
                if key in self.kv_store:
                    response['doesExist'] = True
                    response['message'] = myconstants.RETRIEVED_MESSAGE
                    response['value'] = self.kv_store[key]
                    response['causal-context'] = self.causal_context
                    code = 200
                else:
                    response['doesExist'] = False
                    response['message'] = myconstants.GET_ERROR_MESSAGE
                    response['error'] = myconstants.KEY_ERROR
                    response['causal-context'] = self.causal_context

                return jsonify(response), code
            else:
                """
                    Need to ask other nodes of each shard
                    NOTE: need to make sure we communicate with at least
                          one node for each shard
                """
                proxy_path = 'proxy/kvs/keys'

                partition = self.all_partitions[correct_shard_id]

                for node_address in partition:
                    url = os.path.join('http://', node_address, proxy_path, key)

                    try:
                        resp = requests.get(url, json=contents, timeout=myconstants.TIMEOUT)

                        return resp.text, resp.status_code
                    except (requests.Timeout, requests.exceptions.ConnectionError):
                        """
                            We were not able to connect to another node, maybe node is
                            down? Thus continue to try and contact other nodes for a
                            certain shard
                        """
                        continue

                # TODO handle 503 (timeout errors)

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
                # Error: Invalid Json format, which shouldn't happen for this assignment
                return jsonify(myconstants.BAD_FORMAT_RESPONSE), 400

            correct_shard_id = self.currentHashRing.get_node(key)

            # key mapped to current shard
            if correct_shard_id == self.shard_id:

                # first verify length of key
                if len(key) > myconstants.KEY_LENGTH:
                    response['message'] = 'Error in PUT'
                    response['error'] = 'Key is too long'
                    response['causal-context'] = self.causal_context
                    code = 400
                    return jsonify(response), code

                # attempt to get value from PUT request
                try:
                    value = contents['value']
                except:
                    # Error: Key value did not exist
                    response['message'] = 'Error in PUT'
                    response['error'] = 'Value is missing'
                    response['causal-context'] = self.causal_context
                    code = 400
                    return jsonify(response), code

                if key in self.kv_store:
                    message = myconstants.UPDATED_MESSAGE
                    code = 200
                    replaced = True
                else:
                    message = myconstants.ADDED_MESSAGE
                    code = 201
                    replaced = False

                self.kv_store[key] = value

                """
                    Updating the causal-context object for the current node with the updated value
                """
                self.handle_causal_context(key, value)

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
                        # TODO *create new json containing new causal context + data*
                        resp = requests.put(url, json=request.get_json(), timeout=myconstants.TIMEOUT)

                    except (requests.Timeout, requests.exceptions.ConnectionError):
                        print('we were not able to communicate with another replica')

                response['replaced'] = replaced
                response['message'] = message
                response['causal-context'] = self.causal_context

                return jsonify(response), code

            else:
                proxy_path = 'proxy/kvs/keys'

                for node_address in self.all_partitions[correct_shard_id]:
                    url = os.path.join('http://', node_address, proxy_path, key)

                    try:
                        resp = requests.put(url, json=contents, timeout=myconstants.TIMEOUT)

                        return resp.text, resp.status_code
                    except (requests.Timeout, requests.exceptions.ConnectionError):
                        continue

                ###### TODO check if need to handle 503 here or not?
                return resp.text, resp.status_code
        """
            DELETE requests handling
        """
        if request.method == 'DELETE':

            correct_shard_id = self.currentHashRing.get_node(key)
            
            if correct_shard_id == self.shard_id:
            # if key in self.kv_store:
                # Need to delete key value from store
                del self.kv_store[key]
                
                """
                    Updating the causal-context object for the current node with the updated value
                """
                try:
                    key_causal_context = self.causal_context[key]
                    key_causal_context['timestamp'] = time.time()
                    key_causal_context['value'] = None
                    key_causal_context['doesExist'] = False
                except KeyError:
                    """
                        If key does not exist in the causal-context object
                    """
                    key_causal_context = {}
                    key_causal_context['timestamp'] = time.time()
                    key_causal_context['value'] = None
                    key_causal_context['doesExist'] = False
                
                self.causal_context[key] = key_causal_context



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
                        # TODO *create new json containing new causal context + data*
                        resp = requests.delete(url, json=request.get_json(), timeout=myconstants.TIMEOUT)

                    except (requests.Timeout, requests.exceptions.ConnectionError):
                        print('we were not able to communicate with another replica')



                response['causal-context'] = self.causal_context
                response['doesExist'] = False
                response['message'] = myconstants.DELETE_SUCCESS_MESSAGE

                code = 200

            else:
                proxy_path = 'proxy/kvs/keys'

                # for shard_id in self.all_partitions:
                #     if shard_id == self.shard_id:
                #         continue

                for node_address in self.all_partitions[correct_shard_id]:
                    url = os.path.join('http://', node_address, proxy_path, key)

                    try:
                        resp = requests.delete(url, json=contents, timeout=myconstants.TIMEOUT)

                    except (requests.Timeout, requests.exceptions.ConnectionError):
                        continue
                        

                ###### TODO check if need to handle 503 here or not?
                return resp.text, resp.status_code

            # else:
            #     """
            #         Need to ask other nodes if they have the key
            #     """
            #     proxy_path = 'proxy/kvs/keys'

            #     for node_address in self.view:
            #         # don't execute loop if node_address is address of current shard node
            #         if node_address == self.address:
            #             continue

            #         url = os.path.join('http://', node_address, proxy_path, key)

            #         try:
            #             resp = requests.delete(url, timeout=myconstants.TIMEOUT)
            #             resp_dict = json.loads(resp.text)

            #             if resp_dict['doesExist'] == True:
            #                 """
            #                     We found the key on another Shard Node
            #                     now forward response back to client
            #                 """
            #                 return resp.text, resp.status_code


            #         except (requests.Timeout, requests.exceptions.ConnectionError):
            #             # Shard Node we are forwarding to was down

            #             error = 'Main instance is down'
            #             message = 'Error in PUT'
            #             status_code = 503
            #             res_dict = {'error': error, 'message': message}

            #             return jsonify(res_dict), status_code

                # response['doesExist'] = False
                # response['error'] = myconstants.KEY_ERROR
                # response['message'] = myconstants.DELETE_ERROR_MESSAGE
                # code = 404

            # return jsonify(response), code


    def proxy_keys(self, key):
        """
        Method similar to keys, but instead it does not ask other nodes about a key.
        proxy_keys just returns whether it finds its key in it's local storage or not
        """
        response = {}
        contents = request.get_json()
        # context = contents['causal-context']
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
                response['causal-context'] = self.causal_context
                code = 200
            else:
                response['doesExist'] = False
                response['error'] = myconstants.KEY_ERROR
                response['message'] = myconstants.GET_ERROR_MESSAGE
                response['address'] = self.address
                response['causal-context'] = self.causal_context
                code = 404

            return jsonify(response), code

        """
            PUT requests handling forward from another shard node
        """
        if request.method == 'PUT':
            contents = request.get_json()
            # context = contents['causal-context']

            if len(key) > myconstants.KEY_LENGTH:
                response['message'] = 'Error in PUT'
                response['error'] = 'Key is too long'
                response['causal-context'] = self.causal_context
                response['address'] = self.address
                code = 400
                return jsonify(response), code

            if key in self.kv_store:
                replaced = True
                message = myconstants.UPDATED_MESSAGE
                code = 200
            else:
                replaced = False
                message = myconstants.ADDED_MESSAGE
                code = 201

            try:
                value = contents['value']
            except:
                # Error: Key value did not exist
                response['message'] = 'Error in PUT'
                response['error'] = 'Value is missing'
                response['causal-context'] = self.causal_context
                response['address'] = self.address
                code = 400
                return jsonify(response), code


            """
                Update/Insert the Key
            """
            self.kv_store[key] = value

            """
                Updating the causal-context object for the current node with the updated value
            """
            self.handle_causal_context(key, value)

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
            response['causal-context'] = self.causal_context
            response['address'] = self.address

            return jsonify(response), code
        """
            DELETE requests handling forward from another shard node
        """
        if request.method == 'DELETE':
            if key in self.kv_store:
                # Need to delete key value from store
                del self.kv_store[key]


                """
                    Updating the causal-context object for the current node with the updated value
                """
                try:
                    key_causal_context = self.causal_context[key]
                    key_causal_context['timestamp'] = time.time()
                    key_causal_context['value'] = None
                    key_causal_context['doesExist'] = False
                except KeyError:
                    """
                        If key does not exist in the causal-context object
                    """
                    key_causal_context = {}
                    key_causal_context['timestamp'] = time.time()
                    key_causal_context['value'] = None
                    key_causal_context['doesExist'] = False
                

                self.causal_context[key] = key_causal_context

                response['doesExist'] = False
                response['message'] = myconstants.DELETE_SUCCESS_MESSAGE
                response['address'] = self.address
                response['causal-context'] = self.causal_context

                code = 200


            else:
                response['doesExist'] = False
                response['error'] = myconstants.KEY_ERROR
                response['message'] = myconstants.DELETE_ERROR_MESSAGE
                response['causal-context'] = self.causal_context

                code = 404


            return jsonify(response), code



    def replicate(self, key):
        """
        Function used to handle other nodes receiving a replicated value from
        another node in the same replica
        """
        response = {}
        code = 999
        contents = request.get_json()
        # context = contents['causal-context']
        value = contents['value']

        """
            PUT requests handling forward from another shard node
        """
        if request.method == 'PUT':
            # at this point we have a valid value and key
            if key in self.kv_store:
                replaced = True
                message = myconstants.UPDATED_MESSAGE
                code = 200
            else:
                replaced = False
                message = myconstants.ADDED_MESSAGE
                code = 201

            self.causal_context = contents['causal-context']

            response['replaced'] = replaced
            response['message'] = message
            response['causal-context'] = self.causal_context
            response['address'] = self.address

            self.kv_store[key] = value
        """
            DELETE requests handling forward from another shard node
        """
        if request.method == 'DELETE':
            del self.kv_store[key]

            self.causal_context = contents['causal-context']

            response['doesExist'] = False
            response['message'] = myconstants.DELETE_SUCCESS_MESSAGE
            response['causal-context'] = self.causal_context
            response['address'] = self.address

        return jsonify(response), code

    def handle_causal_context(self, key, value):
        """
        Function used to handle the addition of an event to
        the current causal context
        :param key: key in API call (e.g. http://127.0.0.1:13800/kvs/keys/<key>)
        """
        # Add event to causal context
        try:
            self.causal_context[key] = {}
            self.causal_context[key]['timestamp'] = str(time.time())
            self.causal_context[key]['value'] = value
            self.causal_context[key]['doesExist'] = True
        except:
            print('Error: Issue adding to causal context')
