from flask import Blueprint
from flask import Flask
from flask import request
from flask import jsonify
import myconstants
import os

kv_store = {}

main_blueprint = Blueprint('main_blueprint', __name__)

@main_blueprint.route('/', methods=['GET', 'POST'])
def index():
    return 'Hello, world!'

@main_blueprint.route('/hello', methods=['GET'])
def hello():
    return 'Hello, world!'

@main_blueprint.route('/hello/<string:name>', methods=['POST'])
def hello_name(name):
    return 'Hello, {0}!'.format(name)

@main_blueprint.route('/echo/<string:msg>', methods=['GET', 'POST'])
def echo(msg):
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
