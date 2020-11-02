from flask import Flask
from flask import request

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    return 'Hello, World!'

@app.route('/hello', methods=['GET'])
def hello():
    return 'Hello, World!'

@app.route('/hello/<string:name>', methods=['POST'])
def hello_name(name):
    return 'Hello, {0}!'.format(name)

@app.route('/echo/<string:msg>', methods=['GET', 'POST'])
def echo(msg):
    if request.method =='POST':
        return 'POST message reveived: {0}'.format(msg)
    if request.method == 'GET':
        return 'This method is unsupported.', 405