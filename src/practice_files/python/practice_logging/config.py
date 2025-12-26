import yaml
import logging
from logging.config import dictConfig


def accept_conf():
    with open("python_log_conf.yml") as fd:
        conf = yaml.safe_load(fd)

        dictConfig(conf)

    return logging.getLogger("default_logger")


logger = accept_conf()
