import functools
import itertools
from operator import concat


def func(t, r, s, *args, a, b, c, d, **kwargs):
    print(t, r, s, args, a, b, c, d, kwargs)


def factorial(num):
    """
    this is factorial

    :param num: number
    :type num: int
    :return: new number
    """
    if num > 1:
        return num * factorial(num - 1)
    elif num == 1:
        return 1
    else:
        raise Exception("wrong num range")


if __name__ == "__main__":
    # func(1,2,3,4,5,6,7,8,
    #     **dict(
    #         a=100,
    #         b=300,
    #         c='zxcv',
    #         d='hyte',
    #     )
    # )
    # concat 1
    print(concat("asdf", "zxcv"))

    # concat 2
    print(
        concat(
            [
                1,
                2,
                3,
            ],
            [4, 5, 6],
        )
    )

    # concat 3
    l1 = [1, 2, 3]
    l2 = [3, 4, 5]
    l3 = [4, 5, 6, 7]

    print(list(itertools.chain(l1, l2, l3)))
    print(functools.reduce(concat, [l1, l2, l3]))
