from functools import wraps


def deco1(f):
    """Docstring deco1"""

    def wrapper(*args, **kwargs):
        """Docstring wrapper"""
        print("Calling deco1")
        return f(*args, **kwargs)

    return wrapper


def deco2(f):
    """Docstring deco2"""

    @wraps(f)
    def wrapper(*args, **kwargs):
        """Docstring wrapper"""
        print("Calling deco2")
        return f(*args, **kwargs)

    return wrapper


def deco3(v):
    if isinstance(v, str):
        v += "_str"
    elif isinstance(v, int):
        v += 1000000
    elif isinstance(v, float):
        v /= 150
    else:
        v = v

    return v


@deco1
def sample1():
    """Docstring sample1"""
    print("called sample1")


@deco2
def sample2():
    """Docstring sample2"""
    print("called sample2")


def main():
    print("sample1")
    print("name", sample1.__name__)
    print("docstring", sample1.__doc__)

    print("sample2")
    print("name", sample2.__name__)
    print("docstring", sample2.__doc__)

    @deco2
    @deco1
    def func():
        print("Main func")

    func()


if __name__ == "__main__":
    main()
