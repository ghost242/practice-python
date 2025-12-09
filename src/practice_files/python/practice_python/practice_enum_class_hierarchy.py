import abc
import enum


class AbcCls:
    pass


class Cls(AbcCls, enum.Enum):
    a = enum.auto()
    b = enum.auto()
    c = enum.auto()
    d = enum.auto()
    e = enum.auto()


def main():
    n: AbcCls = Cls.a
    print(n)
    print(issubclass(Cls, (AbcCls,)))
    print(issubclass(Cls, (enum.Enum,)))
    print(issubclass(Cls, (enum.EnumMeta,)))


if __name__ == "__main__":
    main()
