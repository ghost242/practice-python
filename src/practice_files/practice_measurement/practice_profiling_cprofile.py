"""
For practice code profiling and tracing call stack packages in standard library.

target functions:
    - collatz conjugation
    - leibnitz formula for pi
    - factorial(ver. recursive)

outputs:
    * Profiling
        ```
               21181 function calls (7 primitive calls) in 0.353 seconds

         Random listing order was used

         ncalls  tottime  percall  cumtime  percall filename:lineno(function)
              1    0.000    0.000    0.000    0.000 {method 'disable' of '_lsprof.Profiler' objects}
              2    0.333    0.167    0.333    0.167 /.../practice_measurement/practice_profiling_cprofile.py:76(leibniz_formula_pi)
        21000/3    0.019    0.000    0.019    0.006 /.../practice_measurement/practice_profiling_cprofile.py:58(factorial)
          178/1    0.000    0.000    0.000    0.000 /.../practice_measurement/practice_profiling_cprofile.py:65(collatz_conjugation)
        ```

    * call stack
"""

import io
import math
from functools import lru_cache
import pstats
import warnings
from dataclasses import dataclass
from decimal import Decimal, getcontext
import tracemalloc
import cProfile

import sys
import os
from pstats import SortKey
from typing import Dict

import gc

from practice_files.python.practice_builtins.practice_dataclass_from_dict import (
    MetaDataClass,
)
from practice_files.python.practice_func.practice_compisite import (
    composite_funcs,
)


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


def get_pi_approximate(n):
    res = Decimal(0.0)

    for i in range(n):
        series = Decimal(((-1) ** i) / (2 * i + 1))
        res = res + series

    res = res * Decimal(4.0)

    return res


def factorial(n):
    if n <= 1:
        return 1

    return n * factorial(n - 1)


def iter_collatz_conjugation(n):
    it = 0
    while n != 1:
        if n % 2 == 0:
            n = n // 2
        else:
            n = 3 * n + 1

        it += 1

    return it


import time


def recursive_collatz_conjugation(n, it=0):
    if n == 1:
        return it

    if n % 2 == 0:
        n = n // 2
    else:
        n = 3 * n + 1

    time.sleep(0.1)

    return recursive_collatz_conjugation(n, it + 1)


def leibniz_formula_pi(it):
    pi_quarter = 0
    for k in range(it):
        pi_quarter += ((-1) ** k) / (2 * k + 1)

    return 4 * pi_quarter


def add_2(x):
    return x + 2


def multiply(x):
    return x * 2


def sub_2(x):
    return x - 2


def power_2(x):
    return x**2


from practice_files.practice_measurement.profiling import b


def d(n):
    time.sleep(0.4)
    return [c(n // 2) for _ in range(4)]


def c(n):
    time.sleep(0.3)
    return [b(n - 1) for _ in range(3)]


def main():
    # value = dict(
    #     a="hello",
    #     b="10023",
    #     c=str(factorial(100)),
    #     d="world",
    #     e="10,20,30,40,50",
    #     f='{"key1":"val1", "key2":"val2", "key3":"val3"}',
    # )

    profiler = cProfile.Profile()

    try:
        profiler.enable()
        # f = factorial(7000)
        # factorial(7000)
        # iter_collatz_conjugation(123456789)
        recursive_collatz_conjugation(123456789)
        recursive_collatz_conjugation(123456789)
        recursive_collatz_conjugation(123456789)
        # leibniz_formula_pi(1000000)
        # cls.from_dict(value)
        # snapshot1 = tracemalloc.take_snapshot()

        # fac_res = factorial(7000)

        # calc_pi = leibniz_formula_pi(1000000)

        # d(100)

        # snapshot2 = tracemalloc.take_snapshot()
        # print("---" * 9)
        # snapshot = snapshot.filter_traces(
        #     [
        #         tracemalloc.Filter(inclusive=False, filename_pattern="*/python3.13/*"),
        #     ]
        # )
        # df = snapshot2.compare_to(snapshot1, "traceback")
        # for l in df:
        #     print(l)
        # print("---snapshot1---")
        # trace_stat = snapshot1.statistics("lineno")
        # for s in trace_stat:
        #     # print(s.size, s.count, s.traceback.format()[-2:])
        #     print(s)
        # print("==="*9)
        # for tb in trace_stat[:2]:
        #     for line in tb.traceback.format():
        #         print(line)

        # print("---snapshot2---")
        # trace_stat = snapshot2.statistics("traceback")
        # for s in trace_stat:
        #     # print(s.size, s.count, s.traceback.format()[-2:])
        #     print(s)
        #     print("==="*9)

        #     for line in s.traceback.format():
        #         print(line)
        #     print("///" * 6, "\\\\\\" * 6)

    except RecursionError as e:
        print("Too much recursion", str(e))
    finally:
        profiler.disable()

        s = io.StringIO()
        sortby = (
            SortKey.PCALLS,
            SortKey.CUMULATIVE,
        )
        ps = (
            pstats.Stats(profiler, stream=s).strip_dirs()
            # .sort_stats(*sortby)
        )
        ps.print_stats()
        print(s.getvalue())
        # print("---" * 9)
        # ps.print_callers()
        # print(s.getvalue())


if __name__ == "__main__":
    sys.setrecursionlimit(1_000_000_000)
    sys.set_int_max_str_digits(1_000_000_000)
    # tracemalloc.start(25)
    main()
    # tracemalloc.stop()
