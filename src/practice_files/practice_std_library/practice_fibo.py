from practice_measurement.clocker import clocker
import functools


@clocker
def fibonacci(n):
    if n < 2:
        return n
    return fibonacci(n - 2) + fibonacci(n - 1)


@functools.lru_cache()
@clocker
def fibonacci_memoization(n):
    if n < 2:
        return n
    return fibonacci_memoization(n - 2) + fibonacci_memoization(n - 1)


if __name__ == "__main__":
    print(fibonacci(6))

    print(fibonacci_memoization(6))
