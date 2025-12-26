"""
Real(x) = dA * x + B
Solution(x) = A * x + B
"""

import random


def predictor(a, x, b):
    """
    A = parameter A in Real
    x = input value
    B = parameter B in Real
    """
    return a * x + b


def moderator(a, da):
    """
    A = parameter A in Solution
    dA = parameter A in Real
    """
    return a - da


def diff(comp, sol):
    """
    comp = Real(x)
    sol = Solution(x)
    """
    return comp - sol


def propagate(l, e, x):
    """
    (E)rror = Real(x) - Solution(x)
            = (dA * x + b) - (A * x + b)
            = (dA - A) * x
    (L)earning = learning rate
    x = input value
    """
    return l * e / x


def runner():
    points = [(x, x + random.uniform(-1, 1)) for x in range(1, 100)]

    a = 0.5
    b = 0
    l = 1

    for x, sol in points:
        res = predictor(a, x, b)
        err = diff(res, sol)
        da = propagate(l, err, x)
        a = moderator(a, da)
        print(f"{res=}, {err=}, {a=}")

    print(f"f(x) = {a} * x + b")


if __name__ == "__main__":
    runner()
