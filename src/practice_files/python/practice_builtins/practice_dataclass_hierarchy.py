from dataclasses import dataclass, field


class SomeClassA:
    pass


class SomeClassB:
    pass


@dataclass
class ParentClass:
    a: int = field()
    b: SomeClassA = field(init=False)
    __c: str = field(init=False, default="xx")


@dataclass
class ChildClass(ParentClass):
    b: SomeClassB = field(default=None)
    c: int = field(default=None)
    d: str = field(default=None)
    e: list = field(default=None)


def main():
    c = ChildClass(
        10,
        SomeClassB(),
        10,
        "asdf",
        [
            1,
            2,
            3,
        ],
    )
    print(c)


if __name__ == "__main__":
    main()
