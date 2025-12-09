import logging
from logging.config import listen, stopListening, dictConfig


def log_test():
    logger_thread = listen(8000)

    dictConfig(logger_thread)

    logger = logging.getLogger("default_logger")

    logger.error("Hello!")

    stopListening()

if __name__=="__main__":
    log_test()

