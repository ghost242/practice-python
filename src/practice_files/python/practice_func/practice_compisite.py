"""
Implementation function composition
"""

import logging

from typing import Callable
from functools import reduce


def composite_funcs(*funcs: Callable) -> Callable:
    # def comp(f, g):
    #     logging.debug("%s(%s(x))", f.__name__, g.__name__)
    #     return lambda x: f(g(x))

    # rev_funcs = tuple(reversed(funcs))
    # return reduce(comp, rev_funcs[1:], rev_funcs[0])
    # return reduce(lambda f, g: (lambda x: f(g(x))), funcs[1:], funcs[0])
    # return reduce(lambda f, g: (lambda x: f(g(x))), funcs)
    # msg = ",".join(["{}".format(func.__name__) for func in funcs])
    # logging.debug(msg)
    # func = lambda x: funcs[0](composite_funcs(*funcs[1:])(x)) if len(funcs) > 1 else funcs[0]

    # return lambda x: funcs[0](composite_funcs(*funcs[1:])(x)) if len(funcs) > 1 else funcs[0]
    return funcs[0] if len(funcs) == 1 else lambda x: funcs[0](composite_funcs(*funcs[1:])(x))
    # if len(funcs) > 1:
    #     composited_func = composite_funcs(*funcs[1:])
    #     res_func = lambda x: funcs[0](composited_func(x))
    #     res_func.__name__ = f"{funcs[0].__name__}.{composited_func.__name__}"
    #     return res_func
    # else:
    #     return funcs[0]

    # if len(funcs) > 2:
    #     func, *sub_funcs = funcs
    #     return lambda x: func(composite_funcs(*sub_funcs)(x))
    # elif len(funcs) ==2 :
    #     func_1, func_2 = funcs
    #     return lambda x: func_1(func_2(x))
    # else:
    #     return funcs[0]

    # comped_func = funcs[-1]

    # for func in funcs[:-2]:
    #     comped_func = comp(func, comped_func)
    # return comped_func


def main():
    def add_2(x):
        logging.debug("%d + 2 = %d", x, x + 2)
        return x + 2

    def multiply(x):
        logging.debug("%d * 2 = %d", x, x * 2)
        return x * 2

    def sub_2(x):
        logging.debug("%d - 2 = %d", x, x - 2)
        return x - 2

    def power_2(x):
        return x ** 2

    # composited_funcs = composite_funcs(power_2, power_2, power_2, power_2, power_2)

    # f(x) = x+2, g(x) = x*2, f(g(f(x))) = (x+2)*2+2, f(g(f(2))) = 10
    composited_funcs = composite_funcs(add_2, multiply, add_2)
    print("function result: ", composited_funcs(2))

    # f(x) = x+2, g(x) = x*2, h(x) = x-2, f(g(h(x))) = (x-2)*2+2, f(g(h(2))) = 2
    composited_funcs = composite_funcs(add_2, multiply, sub_2)
    print("function result: ", composited_funcs(2))

    composited_funcs: Callable[[int], int] = composite_funcs(power_2)
    print("function result: ", composited_funcs(2))
    
    # print(type(composited_funcs), composited_funcs.__name__)
    # print("file name: ", composited_funcs.__name__)


if __name__ == "__main__":
    # logging.getLogger().setLevel(logging.DEBUG)
    main()
