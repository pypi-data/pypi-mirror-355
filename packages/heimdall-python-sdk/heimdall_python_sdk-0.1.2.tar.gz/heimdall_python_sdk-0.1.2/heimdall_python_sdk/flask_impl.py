from flask import jsonify, make_response
from .core import get_memory_payload

def register_ping(app, route="/__ping__"):
    @app.route(route, methods=["GET", "OPTIONS"])
    def ping():
        response = make_response(jsonify(get_memory_payload()))
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        return response
