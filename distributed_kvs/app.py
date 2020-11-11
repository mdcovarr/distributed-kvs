"""
    Main entrance of REST Server

    Need to determine if there is a FORWARDING_ADDRESS value in the
    environment. If yes, we start a 'follower' or 'proxy' node.
    If no, we start a 'main' node.
"""

from flask import Flask
from flask import request
from flask import jsonify
import os
from main_app import main_blueprint
from proxy_app import proxy_blueprint

if __name__ == '__main__':
    """
        Code main entrance
    """
    app = Flask(__name__)


    FORWARDING_ADDRESS = os.environ.get('FORWARDING_ADDRESS')

    if FORWARDING_ADDRESS and FORWARDING_ADDRESS != '':
        app.register_blueprint(proxy_blueprint)
    else:
        app.register_blueprint(main_blueprint)

    app.run(host='0.0.0.0', port=13800)
