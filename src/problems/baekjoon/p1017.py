import numpy as n
def prime(under: int):
    p = []
    for i in range(2, under):
        for n in p:
            if i % n == 0:
                break
        else:
            p.append(i)
    return p

def make_pair(arr):
    """
    0, 1 -> 2, 3 -> 4, 5
         -> 2, 4 -> 3, 5
         -> 2, 5 -> 3, 4
    """
    for i in range(len(arr)):
        yield arr[i], arr[(i+1) % len(arr) ]

if __name__ == "__main__":
    nums = int(input())

    arr = list(map(int, input().split()))
    used = []

    for i, n in enumerate(arr):
        