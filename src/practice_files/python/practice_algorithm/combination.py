"""
ex) 1,2,3,4,5,6,7,8,9,10
Make combination set as pair
"""

from copy import copy


def probability_cases(arr, *, n=2):
    def _inner_func(items, *, comb=[]):
        nonlocal res

        if len(items) <= n:
            res.append(comb + [tuple(items)])

        else:
            _items = copy(items)
            v1 = _items.pop(0)
            for i in range(len(_items)):
                v2 = _items[i]
                _inner_func(
                    _items[:i] + _items[i + 1 :], comb=(comb + [(v1, v2)])
                )

    res = []

    _inner_func(arr)

    return res


def probability_cases_2(arr, *, n=2):
    def _inner_reverse_sublist(ls: list, start, window_size):
        return (
            ls[:start]
            + list(reversed(ls[start : start + window_size]))
            + ls[start + window_size :]
        )

    def _inner_slicer(ls: list, window_size):
        comb = []
        while ls:
            comb.append(tuple(ls[:window_size]))
            ls = ls[window_size:]

        return comb

    def _inner_func(
        items,
    ):
        nonlocal res

        res.append(_inner_slicer(items, n))

        for step in range(2, len(items)):
            for i in range(len(items) - step):
                _items = _inner_reverse_sublist(items, i, step)

                res.append(_inner_slicer(_items, n))

    res = []

    _inner_func(arr)

    return res


if __name__ == "__main__":
    sample = [
        1,
        2,
        3,
        4,
        5,
        6,
        7,
        8,
        # 9,10,11,12,
        # 13,14,15,16,
    ]

    # print(probability_cases(sample))
    print(probability_cases_2(sample))
