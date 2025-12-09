import typing

NT = typing.TypeVar("NT", bound="int")

CT = typing.TypeVar("CT", bound="[int] > 100")


def func(val: str) -> NT:
    # return int(val)
    return val


n: CT = 0


def main():
    t = typing.Union[int, str]

    # print(t)
    # print(dir(t))
    # print(type(t))
    if isinstance(t, type):
        print(t)
    else:
        print(t.__args__)
        print(getattr(t, "__args__"))

    n = typing.cast(int, "10")
    print(n, type(n))

    ta = typing.Any
    print(ta)
    print(ta == typing.Any)
    # print(isinstance(ta, typing.Any))
    # print(*[(n, getattr(ta, n)) for n in dir(ta)], sep="\n")

    l: NT = "asdf"
    l: NT = 100
    l: NT = 1.123


if __name__ == "__main__":
    main()
