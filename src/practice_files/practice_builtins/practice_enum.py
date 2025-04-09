import enum


class cls(enum.Enum):
    a = enum.auto()
    b = enum.auto()


def main():
    print(cls["a"].value)
    print("b" in dir(cls))


if __name__ == "__main__":
    main()
