import time
import functools
import logging


def clocker(func):
    acc_sec = 0.0

    @functools.wraps(func)
    def clocked(*args, **kwargs):
        nonlocal acc_sec
        t0 = time.time()
        result = func(*args, **kwargs)
        elapsed = time.time() - t0
        acc_sec += elapsed
        name = func.__name__
        arg_lst = []
        if args:
            arg_lst.append(", ".join(repr(arg) for arg in args))
        if kwargs:
            pairs = ["%s=%r" % (k, w) for k, w in sorted(kwargs.items())]
            arg_lst.append(", ".join(pairs))
        arg_str = ", ".join(arg_lst)
        logging.info(
            "[%3.8fs | %3.8fs] %s(%s) ->  "
            % (
                acc_sec,
                elapsed,
                name,
                arg_str,
            )
        )
        return result

    return clocked
