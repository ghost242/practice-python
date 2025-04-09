from tools.clocker import clocker


def f(n):
    return int(n / 2) if n % 2 == 0 else (3 * n + 1)


def collatz(n):
    k = n
    while True:
        yield k
        if k == 1:
            break
        k = f(k)


@clocker
def get_maximum(begin, end):
    print("Maximum number")
    res = list()
    for i in range(begin, end):
        l = []
        g = collatz(i)
        for v in g:
            l.append(v)
        m = max(l)
        res.append((i, m))
    return res


@clocker
def get_meet_point(begin, end, number):
    values = []
    for i in range(begin, end):
        for v in collatz(i):
            if number == v:
                values.append(i)
                break
    if len(values) == 0:
        return f"No one has {number}."
    else:
        return f"Include {number}: {values}"


@clocker
def get_all_series(n):
    return [[i for i in collatz(t)] for t in range(2, n)]


def main():
    get_all_series(2000000)


if __name__ == "__main__":
    main()


from functools import reduce, partial

join_by_sep = partial(reduce, lambda a, b: f"{a},{b}")
