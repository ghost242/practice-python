import logging
import sys

if __name__ == "__main__":
    log = logging.getLogger("sample_logger")

    print(logging.root, log, "\n", sep="\n")

    logging.basicConfig(level=logging.INFO)

    print(logging.root, log, "\n", sep="\n")

    log.setLevel(logging.ERROR)
    print(logging.root, log, "\n", sep="\n")
