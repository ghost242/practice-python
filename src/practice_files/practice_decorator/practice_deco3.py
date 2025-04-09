import logging
from functools import wraps
import importlib.util


class DecoFunc:
    def __init__(self, *args):
        # decorator arguments
        # print(*args)
        pass

    def __call__(self, *args, **kwargs):
        # function instance
        f, *p = args

        @wraps(f.__name__)
        def inline_func():
            print("This is inner function")
            f()

        return inline_func


class DecoCls:
    def __init__(self, *args):
        print("DecoCls.__init__")
        for arg in args:
            self.__dict__[arg] = arg
        # self.deco_args = args

    def __call__(self, *args, **kwargs):
        print("DecoCls.__call__")
        c, *p = args
        dicts = dict(**c.__dict__)

        if "__slots__" in dicts:
            for v in dicts["__slots__"]:
                dicts.pop(v)
            dicts["__slots__"] = (*dicts["__slots__"], *self.__dict__.keys())
        else:
            dicts["__slots__"] = tuple(self.__dict__.keys())

        def __new(cls):
            # c.__init__(cls)
            for k in self.__dict__.keys():
                spec = importlib.util.find_spec(k)
                if spec:
                    c.__setattr__(cls, k, spec.loader.load_module())
                else:
                    logging.warning(f"This package({k}) is not found.")

        print(f"DecoCls.__call__::inner_cls.name: {c.__name__}")
        inner_cls = type(c.__name__, c.__bases__, dicts)
        inner_cls.__init__ = __new

        return inner_cls


class prim_cls:
    def __init__(self):
        print("prim_cls.__init__")


@DecoCls("requests")
class cls(prim_cls):
    __slots__ = ("x", "y", "z")

    def __init__(self):
        super().__init__(self)
        self.x = 10
        self.y = 20
        self.z = 30
        print("cls object __init__")

    def mem_func(self):
        print("mem_func")


@DecoFunc(1, 2, 3)
def func():
    print("hello world!!")


class Aa:
    def __init__(self):
        self.a = 1
        self.b = 2


if __name__ == "__main__":
    c = cls()
    print(c.x, c.y, c.z)
    res = c.requests.get("https://www.google.com")

    print(res.url, res.status_code)

if "a" in "zzxcv" and "b" in "reiyhowert" and 100 == int("100"):
    pass
