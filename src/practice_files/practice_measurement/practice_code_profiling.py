import io
import math
import pstats
import warnings
from dataclasses import dataclass
from decimal import Decimal, getcontext
import tracemalloc
import cProfile

import sys
from pstats import SortKey
from typing import Dict

from practice_files.practice_dataclass import MetaDataClass


@dataclass
class cls(metaclass=MetaDataClass):
    a: str
    b: int
    c: int
    d: str
    e: list
    f: Dict[str, str]


def print_traceback(t: tracemalloc.Trace):
    print(t.domain, t.size)
    for line in t.traceback:
        print(f"\t{line}")


def get_pi(n):
    res = Decimal(3)

    latest_num = Decimal(2)
    for i in range(n):
        series = (
            ((-1) ** i)
            * 4
            / (latest_num * (latest_num + 1) * (latest_num + 2))
        )
        latest_num = latest_num + 2
        res = res + series

    return res


def get_factorial(n):
    if n > 1:
        return n * get_factorial(n - 1)
    else:
        return 1


def get_series(n):
    bucket = list()
    while True:
        if n == 1:
            bucket.append(1)
            break

        if n % 2 == 0:
            n = int(n / 2)
        else:
            n = int(3 * n + 1)
        bucket.append(n)
    return bucket


def main():
    getcontext().prec = 2
    sys.setrecursionlimit(100000)

    value = dict(
        a="hello",
        b="10023",
        c=str(get_factorial(100)),
        d="world",
        e="10,20,30,40,50",
        f='{"key1":"val1", "key2":"val2", "key3":"val3"}',
    )

    profiler = cProfile.Profile()

    tracemalloc.start()

    profiler.enable()
    # res = get_factorial(10000)
    # res = get_pi(1000000)
    # res = [get_series(i) for i in range(1000000)]
    # print(res)

    # c = cls.from_dict(value)
    # print(c)
    warnings.warn("Test wwarning", UserWarning)

    snapshot = tracemalloc.take_snapshot()

    profiler.disable()
    tracemalloc.stop()

    s = io.StringIO()
    sortby = SortKey.CUMULATIVE
    ps = pstats.Stats(profiler, stream=s).sort_stats(sortby)
    ps.print_stats()
    print(s.getvalue())

    # stat = snapshot.statistics("traceback", )
    traces = snapshot.filter_traces(
        [tracemalloc.Filter(inclusive=False, filename_pattern="*/python3.8/*")]
    )
    stat = traces.statistics("traceback", False)
    for s in stat:
        print(s.size, s.count)
        print(*s.traceback.format())


if __name__ == "__main__":
    main()
