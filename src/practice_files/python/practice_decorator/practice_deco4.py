"""
Decorator function for class methods and class member variables
"""

from functools import wraps


class DecoFunc:
    def __init__(self, *args, **kwargs):
        pass

    def __call__(self, *args, **kwargs):
        f, *p = args

        @wraps(f.__name__)
        def inline_func():
            setattr(f, self.func.__name__, self.func)

        return inline_func()

    def func(self, *args, **kwargs):
        print(dir(self))
        for k in dir(self):
            print(k, getattr(self, k))
        print(args)
        print(kwargs)


class cls:
    _a: str
    _b: int
    _c: float

    def __init__(self, a="asdf", b=100, c=1.234):
        self._a = a
        self._b = b
        self._c = c

    @DecoFunc
    @property
    def a(self):
        return self._a

    # @deco_func
    @property
    def b(self):
        return self._b

    # @deco_func
    @property
    def c(self):
        return self._c


def main():
    c = cls()

    print(c.a)
    print(type(c.a))
    print(dir(c.a))
    print(c.a.func(1, 2, 3, v1="adf", v2="etq"))


if __name__ == "__main__":
    main()
