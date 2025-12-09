import enum
from typing import NamedTuple


class cls(enum.Enum):
    a: str = "asdf"
    b: str = "zxcv"
    c: str = "qwer"

    # @classmethod
    # def __getattr__(cls, item):
    #     print(f"get {item}")
    #     v = super(enum.Enum).__getattribute__(item).value
    #     print(f"value is v")
    #     return v
    def __get__(self, instance, owner):
        print(instance, owner)
        print(dir(instance))
        print(dir(owner))
        return self.value


def main():
    x = cls.a
    print(x)


if __name__ == "__main__":
    main()
