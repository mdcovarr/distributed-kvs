"""
    Main entrance of REST Server


    VIEW and ADDRESS environment variables will be set in deployment
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

    parser.add_argument('-v', '--view', dest='view', default='',
        help='Initial view for the distributed key value store shards')

    parser.add_argument('-r', '--repl-factor', dest='repl_factor', type=int, default=1,
         help='Argument used to determine the replication factor for the distributed key-value store')

    return parser.parse_args()

if __name__ == '__main__':
    """
        Code main entrance
    """
    args = handle_args()
    app = ShardNodeWrapper(args.ip, args.port, args.view, args.repl_factor)
    app.setup_routes()
    app.setup_address()
    app.setup_view()
    app.setup_repl_factor()
    app.setup_pototetial_replicas()
    app.setup_gossip()
    app.run()
