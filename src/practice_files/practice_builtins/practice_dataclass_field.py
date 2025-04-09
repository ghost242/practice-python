from dataclasses import dataclass, fields, Field
from typing import Tuple


@dataclass
class cls:
    a: str
    b: str
    c: str

    def values(self):
        # type: () -> Tuple[Field, ...]
        return fields(self)


def main():
    c = cls("adf", "zcxv", "ertqe")

    v = c.values()

    print(v[0])


if __name__ == "__main__":
    main()
