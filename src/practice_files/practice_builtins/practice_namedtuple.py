from collections import namedtuple
from typing import NamedTuple


nt = namedtuple("CustomTuple", ["a", "b", "c"])


class ClassTuple:
    rows: int
    cols: int


def func(n: NamedTuple):
    print(n, n._fields)
    print(type(n)._fields)


def main():
    print(nt._fields)
    # func(nt)
    n = nt(10, 20, 30)
    func(n)


if __name__ == "__main__":
    main()
