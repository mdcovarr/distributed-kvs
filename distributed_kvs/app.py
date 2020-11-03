from flask import Flask
from flask import request
from flask import jsonify

kv_store = {}
KEY_LENGTH = 50
ADDED_MESSAGE = 'Added successfully'
UPDATED_MESSAGE = 'Updated successfully'
RETRIEVED_MESSAGE = 'Retrieved successfully'
KEY_ERROR = 'Key does not exist'
GET_ERROR_MESSAGE = 'Error in GET'
DELETE_SUCCESS_MESSAGE = 'Deleted successfully'
DELETE_ERROR_MESSAGE = 'Deleted successfully'

MISSING_RESPONSE = {
    "error": "Value is missing",
    "message": "Error in PUT"
}

BAD_FORMAT_RESPONSE = {
    "error": "Bad json format",
    "message": "Error in PUT"
}

ADD_AND_REPLACE_RESPONSE = {
    "message": "Added successfully",
    "replaced": False
}

LONG_KEY_RESPONSE = {
    "error": "Key is too long",
    "message": "Error in PUT"
}

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    return 'Hello, world!'

@app.route('/hello', methods=['GET'])
def hello():
    return 'Hello, world!'

@app.route('/hello/<string:name>', methods=['POST'])
def hello_name(name):
    return 'Hello, {0}!'.format(name)

@app.route('/echo/<string:msg>', methods=['GET', 'POST'])
def echo(msg):
    if request.method =='POST':
        return 'POST message received: {0}'.format(msg)
    if request.method == 'GET':
        return 'This method is unsupported.', 405

@app.route('/kvs/<string:key>', methods=['GET', 'PUT', 'DELETE'])
def kvs(key):
    response = {}
    code = None

    if request.method == 'PUT':

        try:
            content = request.get_json()
        except:
            # Error: Invalid Json format
            return jsonify(BAD_FORMAT_RESPONSE), 400

        try:
            value = content['value']
        except:
            # Error: Key value did not exist
            return jsonify(MISSING_RESPONSE), 400

        if len(key) > KEY_LENGTH:
            return jsonify(LONG_KEY_RESPONSE), 400

        # at this point we have a valid value and key
        if key in kv_store:
            replaced = True
            message = UPDATED_MESSAGE
            code = 200
        else:
            replaced = False
            message = ADDED_MESSAGE
            code = 201

        response['replaced'] = replaced
        response['message'] = message

        kv_store[key] = value

        return jsonify(response), code

    if request.method == 'GET':
        if key in kv_store:
            response['doesExist'] = True
            response['message'] = RETRIEVED_MESSAGE
            response['value'] = kv_store[key]
            code = 200
        else:
            response['doesExist'] = False
            response['error'] = KEY_ERROR
            response['message'] = GET_ERROR_MESSAGE
            code = 404

        return jsonify(response), code

    if request.method == 'DELETE':
        if key in kv_store:
            # Need to delete key value from store
            del kv_store[key]

            response['doesExist'] = True
            response['message'] = DELETE_SUCCESS_MESSAGE
            code = 200
        else:
            response['doesExist'] = False
            response['error'] = KEY_ERROR
            response['message'] = DELETE_ERROR_MESSAGE
            code = 404

        return jsonify(response), code

if __name__ == '__main__':
    app.run(host='localhost', port=13800)
