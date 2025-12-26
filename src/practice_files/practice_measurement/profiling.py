import time


def b(n):
    time.sleep(0.2)
    return [a(n * 3) for _ in range(2)]


def a(n):
    time.sleep(0.1)
    return n + 100
