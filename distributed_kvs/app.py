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
    parser = argparse.ArgumentParser(description='Server Accepting and Sending Encrypt/Decrypt Request')

    parser.add_argument('IP', help='IP Address to use for client to connect to, or server to listen on')

    parser.add_argument('PORT', type=int,
                        help='Port for server to listen on')

    return parser.parse_args()

if __name__ == '__main__':
    """
        Code main entrance
    """
    args = handle_args()
    app = ShardNodeWrapper(args.IP, args.PORT)
    app.setup_routes()
    app.setup_view()
    app.run()
