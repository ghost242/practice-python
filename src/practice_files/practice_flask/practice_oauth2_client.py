import logging

from flask import Flask, request

app = Flask(__name__)


@app.route("/auth")
def acc_token():
    auth_info = request.args

    logging.debug(auth_info)

    return dict(auth_code=auth_info["auth_code"])


@app.route("/")
def conn_test():
    return "Hello client!!"


if __name__ == "__main__":
    logging.getLogger().setLevel(logging.DEBUG)

    app.run(port=5000, debug=True)
