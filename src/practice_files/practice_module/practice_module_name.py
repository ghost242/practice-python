class Cls:
    class NCls:
        class NNCls:
            pass


def func(obj):
    print(obj.__module__ + "." + obj.__qualname__)
