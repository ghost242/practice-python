import csv
from collections import namedtuple

nt = namedtuple("NT", ("a", "b", "c"))


def write_data():
    data = [
        nt(**{"a": 1, "b": 2, "c": "asdf"}),
        nt(**{"a": 11, "b": 22, "c": "zxcv"}),
        nt(**{"a": 111, "b": 222, "c": "qwer"}),
        nt(**{"a": 1111, "b": 2222, "c": "qaz"}),
        nt(**{"a": 11111, "b": 22222, "c": "wsx"}),
        nt(**{"a": 111111, "b": 222222, "c": "edc"}),
        nt(**{"a": 1111111, "b": 2222222, "c": "rfv"}),
        nt(**{"a": 11111111, "b": 22222222, "c": "tgb"}),
    ]
    with open("test.csv", "w", newline="") as csv_writer:
        writer = csv.writer(
            csv_writer,
            delimiter=",",
            quoting=csv.QUOTE_NONNUMERIC,
        )
        writer.writerows(data)


def main():
    write_data()


if __name__ == "__main__":
    main()
