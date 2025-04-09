"""
주어지는 array의 index와 array[index]의 값을 좌표에 그렸을때
두 점을 잇는 직선과 x절편부터 (x,y)까지 선분이 서로 접하거나 겹치지 않는 모든 점의 수가 가장 많이 나타나는 지점으로부터 직선의 수를 구하는 문제

>>> 1 5 3 2 6 3 2 6 4 2 5 7 3 1 5
<<< 7

arr[11] -> 7인 (11,7)에서 index = {4, 7, 8, 10, 12, 13, 14}까지 잇는 직선이 조건을 만족함. 따라서 답이 7.

                                 |
            |        |           |
   |        |        |        |  |        |
   |        |        |  |     |  |        |
   |  |     |  |     |  |     |  |  |     |
   |  |  |  |  |  |  |  |  |  |  |  |     |
|  |  |  |  |  |  |  |  |  |  |  |  |  |  |
                                 ^          : 가장 많은 직선을 찾을 수 있는 index
            ^        ^  ^     ^     ^  ^  ^ : 위의 index와 직선을 만들 수 있는 선분

"""
from typing import Callable
import logging


def gen_f(x1,y1, x2, y2) -> Callable:
    a = (y2 - y1) / (x2 - x1)
    b = y1 - a * x1
    return lambda x: a * x + b

def mean(arr):
    return sum(arr) / len(arr)

def median(arr):
    _arr = sorted(arr)
    return _arr[len(_arr) // 2]

def check_sight(arr):
    def _inside_find_blind(i, h, w, t):
        logging.debug(f"args: {i=}, {h=}, {w=}, {t=}")
        f = gen_f(i, h, w, t)
        for pos in range(i+1, w):
            building_height = arr[pos]
            comp_altitude = f(pos)
            logging.debug(f"{building_height=}, {comp_altitude=}")

            if building_height >= comp_altitude:
                return False
        else:
            logging.debug(f"clear sight from {i=}")
            return True

    whereas = len(arr)-1
    in_sight = 0
    for idx in range(whereas):
        p = _inside_find_blind(idx, arr[idx], whereas, arr[whereas])

        if p:
            in_sight += 1

    return in_sight


if __name__ == "__main__":
    # raw_a = "1000000000 999999999 999999998 999999997 999999996 1 2 3 4 5"
    # raw_a = "1 2 7 3 2"
    # raw_a = "5 5 5 5"
    # raw_a = "10"
    raw_a = "1 5 3 2 6 3 2 6 4 2 5 7 3 1 5"

    a = list(map(int, raw_a.split()))
    # n = int(input())
    # a = list(map(int, input().split()))

    flag = mean(a)
    # flag = median(a)

    tower = [n if n >= flag else 0 for n in a]

    res = 0

    logging.basicConfig(level=logging.DEBUG)

    for idx, height in enumerate(tower):
        res_a = 0
        res_b = 0
        if height != 0:
            # from idx to 0
            logging.debug(f"------from {idx} to 0-------------")
            t = a[:idx+1]
            if len(t) > 1 :
                res_a = check_sight(t)
                logging.debug(f"From {t}, Get {res_a}")
            # from idx to len(a)
            logging.debug(f"------from {idx} to {len(a)}------")
            r = list(reversed(a[idx:]))
            if len(r) > 1:
                res_b = check_sight(r)
                logging.debug(f"From {r}, Get {res_b}")
            logging.debug(f"Compare {res=} with {(res_a + res_b)=}")
            res = max([res, res_a+res_b])
            logging.debug("===" * 9)
    print(res)
