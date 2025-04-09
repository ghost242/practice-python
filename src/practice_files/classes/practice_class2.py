class A:
    class B:
        def __init__(self):
            self.b = "b"

    a: B

    def __init__(self):
        self.a = self.B()


class cls:
    a: int = 100
    b: int = 200
    c: int = 300

    # def __init__(self, a, b, c):
    #     self.a = a
    #     self.b = b
    #     self.c = c


if __name__ == "__main__":
    obj = A()

    print(obj)
    print(obj.a)
    print(obj.a.b)

    c = cls()
    # print(id(c), id(c.a), id(c.b), id(c.c))
    print("c.a", c.a, "c.b", c.b, "c.c", c.c)
    b = cls()
    b.a = "x"
    b.b = "y"
    b.c = "z"
    print(id(cls), id(cls.a), id(cls.b), id(cls.c))
    print(id(c), id(c.a), id(c.b), id(c.c))
    # print(c.a, c.b, c.c)
    print(id(b), id(b.a), id(b.b), id(b.c))
    # print(b.a, b.b, b.c)
    print(
        id("x"),
        id("y"),
        id("z"),
    )
    cls.a = 1.1
    cls.b = 2.2
    cls.c = 3.3
    # print(id(cls), id(cls.a), id(cls.b), id(cls.c))
    # print(id(c), id(c.a), id(c.b), id(c.c))
    print("c.a", c.a, "c.b", c.b, "c.c", c.c)
    # print(id(b), id(b.a), id(b.b), id(b.c))
    print("b.a", b.a, "b.b", b.b, "b.c", b.c)
