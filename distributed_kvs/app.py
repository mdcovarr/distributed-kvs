"""
    Main entrance of REST Server

    Need to determine if there is a FORWARDING_ADDRESS value in the
    environment. If yes, we start a 'follower' or 'proxy' node.
    If no, we start a 'main' node.
"""

from flask import Flask
from flask import request
from flask import jsonify
import argparse
import os
from shard_node import ShardNodeWrapper

def handle_args():
    """
    Function used to handle command line arguments
    """
    parser = argparse.ArgumentParser(description='Application implementing a distributed Key-Value Store')

    parser.add_argument('-i', '--ip', dest='ip', default='0.0.0.0',
        help='IP Address to use for client to connect to, or server to listen on. Value defaults to 0.0.0.0 if no argument provided')

    parser.add_argument('-p', '--port', dest='port', type=int, default=13800,
        help='Port for server to listen on. value defaults to 13800 if no argument provided')

    return parser.parse_args()

if __name__ == '__main__':
    """
        Code main entrance
    """
    args = handle_args()
    app = ShardNodeWrapper(args.ip, args.port)
    app.setup_routes()
    app.setup_address()
    app.setup_view()
    app.run()
