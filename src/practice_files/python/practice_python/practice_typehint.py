import typing

n = 10  # type: int

print(n)


def func(a, b):
    # type: (int, int) -> int
    return int(a) + int(b)


class CLS(int):
    pass


x: CLS = 10  # Type warning

y: CLS = CLS(30)

z: int = CLS(20)


class A:
    pass


class B(A):
    pass


t: A = A()
u: B = A()  # Type warning
v: A = B()
w: B = B()


class C(CLS, A):
    pass


l: C = 10  # Type warning
m: C = CLS(20)  # Type warning
n: C = A()  # Type warning
o: C = C()


print(func(10, 20))

val: typing.Tuple[int] = (1, 2, 3)
val2: typing.Set[float, int] = {1, 2, 3, 4}


def func_n() -> typing.NoReturn:
    print("No return")

    return 10


r = func_n()

print(r)
