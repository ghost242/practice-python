from typing import List, Dict, Text

import json


def extractor(contexts: List[Text]) -> List[Text]:
    units = {}

    for context in contexts:
        if not context.startswith("tests/"):
            units.append(context)

    return units


def read_file(filename):
    with open(filename) as fd:
        return fd.readlines()


def main():
    lines = read_file("fixtures.txt")

    extracted_lines = extractor(lines[9:4026])

    print(extracted_lines[:10])


if __name__ == "__main__":
    main()
