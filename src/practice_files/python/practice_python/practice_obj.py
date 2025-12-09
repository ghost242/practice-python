class cls:
    def __new__(self):
        print("__new__")
        return object.__new__(self)

    def __init__(self):
        print("__init__")

    def __del__(self):
        print("__del__")

    def __call__(self):
        print("__call__")

    def func1(*args):
        print(args)
        return args[0]()

    @staticmethod
    def func2(*args):
        print(args)
        return args[0]

    @classmethod
    def func3(*args):
        print(args)
        return args[0]()


class ccls(cls):
    pass


def main():
    c = ccls()
    # x1 = c.func1(1,2,3)
    # x2 = c.func2(1,2,3)
    # x3 = c.func3(1,2,3)
    print(isinstance(c, cls))
    print(isinstance(c, ccls))
    print(issubclass(ccls, cls))
    print(issubclass(c.__class__, cls))
    print(issubclass(c.__class__, ccls))


if __name__ == "__main__":
    main()
