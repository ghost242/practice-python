from types import FunctionType, MethodType


def singleton(cls):
    def init_fn(self, *args, **kwargs):
        if hasattr(cls, "__init__"):
            super(cls, self).__init__(*args, **kwargs)

    mem_set = {"__init__": init_fn, **dict(cls.__dict__)}
    _DecoCls = type(f"Singleton{cls.__name__}", (cls,), mem_set)

    class _Creator:
        def __init__(self):
            self.__inst = None

        def __call__(self, *args, **kwargs):
            if self.__inst is None:
                self.__inst = _DecoCls(*args, **kwargs)
            return self.__inst

    return _Creator()


@singleton
class Obj:
    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z

    def func(self):
        print(self)

    def __str__(self):
        return f"<class '{self.__class__.__name__}' | x:{type(self.x)}({self.x}), y:{type(self.y)}({self.y}), z:{type(self.z)}({self.z})>"


@singleton
class ObjB:
    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z

    def func(self):
        print(self)

    def __str__(self):
        return f"<class '{self.__class__.__name__}' | x:{type(self.x)}({self.x}), y:{type(self.y)}({self.y}), z:{type(self.z)}({self.z})>"


class a:
    def __init__(self):
        self.aa = 10

    pass


@singleton
class b(a):
    def __init__(self):
        super(a, self).__init__()
        self.bb = 20


def caller_1():
    o = Obj(10, 20, 30)
    o.func()

    print(o)

    return o


def caller_2():
    o = Obj("40", "50", "60")
    o.func()

    print(o)

    return o


if __name__ == "__main__":
    o1 = caller_1()
    o2 = caller_2()

    print(id(o1), id(o2))
    print(o1 == o2)
