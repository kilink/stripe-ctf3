#!./bin/python -O

import argparse
import binascii
import gc
import linecache
import logging
import os.path
import re

import bitsets
import concurrent.futures
import flask
import requests

from flask import Flask, request

import index



app = Flask(__name__)
logging.getLogger("concurrent.futures").addHandler(logging.StreamHandler())
num_clients = 3
port = 9090
app.indexed = False
app.path = None

session = requests.Session()
pool = concurrent.futures.ThreadPoolExecutor(num_clients + 1)

def request_clients(path, params=None):
    results = []
    for i in range(1, num_clients+1):
        url = "http://localhost:%d%s" % (port + i, path,)
        results.append(pool.submit(session.get, *(url,), params=params))
    return [result.result() for result in results]


def _indexer(path):
    ix = index.Index(app.id)
    ix.index_path(path)
    gc.collect()
    gc.disable()
    app.indexed = True
    app.index = ix


@app.route("/index")
def indexer():
    path = request.args["path"]
    app.path = os.path.abspath(path)
    if master:
        for response in request_clients("/index", {"path": path}):
            assert response.ok
        return flask.jsonify({"success": True})
    pool.submit(_indexer, path)
    return flask.jsonify({"success": True})


@app.route("/healthcheck")
def health_check():
    if master:
        for response in request_clients("/healthcheck"):
            assert response.ok
        return flask.jsonify({"success": True})
    return flask.jsonify({"success": True})


@app.route("/")
def query():
    q = request.args["q"]
    results = []
    if master:
        for response in request_clients("/", {"q": q}):
            response.raise_for_status()
            results.extend(response.content.split())
        return flask.jsonify({"success": True, "results": results})
    results = app.index.search(q)
    if app.debug:
        app.logger.info("Node %d: query: %s, results: %s", app.id, q, results)
    return "\n".join(results)


@app.route("/isIndexed")
def is_indexed():
    if master and not app.indexed:
        for response in request_clients("/isIndexed"):
            if not response.json()["success"]:
                return flask.make_response("Nodes are not indexed", 502)
        app.indexed = True
        gc.collect()
        gc.disable()
    return flask.jsonify({"success": app.indexed})


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--master", action="store_true", default=False)
    parser.add_argument("--id", type=int)
    parser.add_argument("--clients", type=int, default=3)
    parser.add_argument("--debug", action="store_true", default=False)
    parser.add_argument("--profile", action="store_true", default=False)

    args = parser.parse_args()
    if args.id:
        port += args.id
    app.id = args.id
    if args.profile:
        from werkzeug.contrib.profiler import ProfilerMiddleware
        app.wsgi_app = ProfilerMiddleware(app.wsgi_app)
    master = args.master
    num_clients = args.clients
    if args.debug:
        handler = logging.FileHandler(
            "search-%s.log" % (str(args.id or "master"),))
        handler.setLevel(logging.INFO)
        handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s '
            '[in %(pathname)s:%(lineno)d]'
        ))
        app.logger.addHandler(handler)
        logging.getLogger().setLevel(logging.INFO)

    app.run(port=port, debug=args.debug)
