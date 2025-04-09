import weakref


class cls_int:
    def __init__(self, val):
        self.n = val

    def __str__(self):
        return str(self.n)

    def __repr__(self):
        return str(self.n)


def func(a, b):
    print(dir(a), a)
    print(dir(b), b)


def weak_func(a, b):
    print(dir(a), a())
    print(dir(b), b())


def main():
    val1 = cls_int(10)
    val2 = cls_int(20)
    func(val1, val2)
    weak_func(weakref.ref(val1), weakref.ref(val2))


if __name__ == "__main__":
    main()
