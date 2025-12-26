import json
from flask import Flask

app = Flask(__name__)


@app.route("/")
def log_conf():
    return json.dumps(
        {
            "version": 1,
            "formatters": {
                "default_fmt": {
                    "format": '{"level":%(levelno)d,"level_name":"%(levelname)s","log_time":"%(asctime)s","process":{"pid":%(process)d,"pname":"%(processName)s"},"thread":{tid":"%(thread)d,"tname":"%(threadName)s"},"module":"%(module)s","function":"%(funcName)s","line_no":%(lineno)d,"message":"%(message)s"}',
                    "datefmt": "%Y-%m-%d %H:%M:%S",
                }
            },
            "handlers": {
                "default_hnd": {
                    "class": "logging.StreamHandler",
                    "formatter": "default_fmt",
                    "stream": "ext://sys.stdout",
                }
            },
            "loggers": {
                "default_logger": {
                    "handlers": ["default_hnd"],
                }
            },
        }
    )


if __name__ == "__main__":
    app.run(port=8000)
