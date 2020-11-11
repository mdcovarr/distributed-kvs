"""
    Flask Blueprint for the 'main' node.

    This file defines api route handler GET, POST and DELETE requests
    to the key value store
"""

from flask import Blueprint
from flask import Flask
from flask import request
from flask import jsonify
import myconstants
import os

kv_store = {} # key value store 

main_blueprint = Blueprint('main_blueprint', __name__)

@main_blueprint.route('/', methods=['GET', 'POST'])
def index():
    """
    Method to handle the root path /
    :return: hello world string
    """
    return 'Hello, world!'

@main_blueprint.route('/hello', methods=['GET'])
def hello():
    """
    Method to handle the path http://0.0.0.0/hello
    :return: hello world string
    """
    return 'Hello, world!'

@main_blueprint.route('/hello/<string:name>', methods=['POST'])
def hello_name(name):
    """
    Method to handle the path http://0.0.0.0/hello/STRING where STRING
    can be any string sequence
    :param name: is the string value after path /hello/
    :return: string with 'Hello, ' prepended to name value.
    """
    return 'Hello, {0}!'.format(name)

@main_blueprint.route('/echo/<string:msg>', methods=['GET', 'POST'])
def echo(msg):
    """
    Method to handle GET and POST requests to http://0.0.0.0/echo/STRING
    where STRING is any string sequence
    :param msg: msg = STRING in url request
    :return: string message and HTTP status code
    """
    if request.method =='POST':
        return 'POST message received: {0}'.format(msg)
    if request.method == 'GET':
        return 'This method is unsupported.', 405

@main_blueprint.route('/kvs/<string:key>', methods=['GET', 'PUT', 'DELETE'])
def kvs(key):
    response = {}
    code = None

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
        if key in kv_store:
            replaced = True
            message = myconstants.UPDATED_MESSAGE
            code = 200
        else:
            replaced = False
            message = myconstants.ADDED_MESSAGE
            code = 201

        response['replaced'] = replaced
        response['message'] = message

        kv_store[key] = value

        return jsonify(response), code

    if request.method == 'GET':
        if key in kv_store:
            response['doesExist'] = True
            response['message'] = myconstants.RETRIEVED_MESSAGE
            response['value'] = kv_store[key]
            code = 200
        else:
            response['doesExist'] = False
            response['error'] = myconstants.KEY_ERROR
            response['message'] = myconstants.GET_ERROR_MESSAGE
            code = 404

        return jsonify(response), code

    if request.method == 'DELETE':
        if key in kv_store:
            # Need to delete key value from store
            del kv_store[key]

            response['doesExist'] = True
            response['message'] = myconstants.DELETE_SUCCESS_MESSAGE
            code = 200
        else:
            response['doesExist'] = False
            response['error'] = myconstants.KEY_ERROR
            response['message'] = myconstants.DELETE_ERROR_MESSAGE
            code = 404

        return jsonify(response), code
