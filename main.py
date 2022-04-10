from uuid import uuid4
from traceback import format_exc
from flask import Flask, render_template, request, redirect, abort, Response
from deta import Deta
from time import time
from os import environ


app = Flask(__name__)
deta = Deta(environ["DETA_PROJECT_KEY"])
pastas = deta.Base("pastas")
errors = deta.Base("errors")


class Pasta:
    def __init__(self, text: str, key: str, secret: str):
        self.text = text
        self.key = key
        self.secret = secret

    def delete(self):
        pastas.delete(self.key)

    @classmethod
    def create(cls, text: str):
        key = str(uuid4())
        secret = str(uuid4())
        pastas.put({"text": text, "secret": secret}, key)
        return cls(text, key, secret)

    @classmethod
    def get_by_secret(cls, secret: str):
        pasta = pastas.fetch({"secret": secret}).items[0]
        return cls(pasta["text"], pasta["key"], pasta["secret"])

    @classmethod
    def get_by_key(cls, key: str):
        pasta = pastas.get(key)
        return cls(pasta["text"], pasta["key"], pasta["secret"])


@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")


@app.route("/api/create", methods=["POST"])
def api_create():
    pasta = Pasta.create(request.form["text"])
    return {"ok": True, "key": pasta.key, "secret": pasta.secret}


@app.route("/create", methods=["POST"])
def create():
    pasta = Pasta.create(request.form["text"])
    return redirect(f"/{pasta.key}")


@app.route("/api/delete", methods=["GET"])
def api_delete():
    Pasta.get_by_secret(request.args["secret"]).delete()
    return {"ok": True}


@app.route("/<string:key>", methods=["GET"])
def get(key):
    try:
        return Response(Pasta.get_by_key(key).text, mimetype="text/plain")
    except:
        abort(404)


@app.route("/raw/<string:key>", methods=["GET"])
def raw(key):
    try:
        return Response(Pasta.get_by_key(key).text, mimetype="text/plain")
    except:
        abort(404)


@app.errorhandler(404)
def not_found(e):
    return render_template("404.html")


@app.errorhandler(Exception)
def error_handler(e):
    error = errors.put(
        {"traceback": format_exc(), "time": int(time()), "key": str(uuid4())}
    )
    return render_template("error.html", error=str(e), code=error["key"])
