import logging
import sys


def deco_func(super_cls):
    called = 0

    class ncls(super_cls):
        def __init__(self, *args):
            nonlocal called

            print("called ncls.__init__")

            super().__init__(*args)

            self.n = called
            called += 1

    ncls.__name__ = f"decorated_{super_cls.__name__}"
    return ncls


# @deco_func
class cls:
    def __init__(self, a=None, b=None):
        print("called cls.__init__")
        self.a = a
        self.b = b

    def __init_subclass__(cls, **kwargs):
        print("called __init__subclass__", cls.__name__)
        print(kwargs)
        cls.logger = logging.getLogger("TEST")
        hnd = logging.StreamHandler(sys.stdout)
        fmt = logging.Formatter(
            "[%(levelname)s] %(funcName)s:%(lineno)s_%(message)s"
        )
        hnd.setFormatter(fmt)
        cls.logger.addHandler(hnd)
        cls.logger.setLevel(logging.INFO)

    def __repr__(self):
        return f"<Class {self.__class__.__name__} | {', '.join([f'{k}: {v}' for k, v in vars(self).items() if not k.startswith('_')])}>"


# @deco_func
class ccls(cls):
    def __init__(self, x, y):
        print("called ccls.__init__")

        super().__init__()
        self.x = x
        self.y = y

        self.logger.info("Hello")


def main():
    c = cls(10, 20)
    cc = ccls(100, 200)

    print(c)
    print(cc)


if __name__ == "__main__":
    main()
