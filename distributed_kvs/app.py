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
from shard_node import ShardNodeWrapper

if __name__ == '__main__':
    """
        Code main entrance
    """
    app = ShardNodeWrapper()
    app.setup_routes()
    app.setup_view()
    app.run()
