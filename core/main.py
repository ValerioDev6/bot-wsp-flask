import os

import environ
from flask import Flask, jsonify, make_response, request

env = environ.Env()
environ.Env.read_env()

app = Flask(__name__)


VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN")


@app.route("/", methods=["GET"])
def index():
    message = environ.os.get("MESSAGE")
    return jsonify({"status": "success", "message": message})


@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    if request.method == "GET":
        mode = request.args.get("hub.mode")
        token = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")

        if mode == "subscribe" and token == VERIFY_TOKEN:
            print("WEBHOOK_VERIFIED")
            return make_response(str(challenge), 200)

        else:
            return make_response("Verification token mismatch", 403)
    elif request.method == "POST":
        data = request.get_json()
        print("Received WebHook  data:", data)
        return jsonify({"status": "success"}), 200


@app.route("/whatsap/message", methods=["POST"])
def ReceiveMessage():
    return ""
