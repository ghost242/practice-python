from typing import Literal, get_args

CellOperator = Literal["up","down","left","right"]

def get_neighbor_of_value(arr, i, j, *, op: CellOperator):
    if op == "up":
        if i == 1:
            return arr[i-1][j]
        else:
            return None
    elif op == "down":
        if i == 0:
            return arr[i+1][j]
        else:
            return None
    elif op == "left":
        return arr[i][j-1]
    elif op == "right":
        return arr[i][j+1]
    else:
        return None

def main():
    cases = int(input())

    for _ in range(cases):
        rows, cap = tuple(map(int, input().split()))
        arr = list(map(int, input().split()))
        arr.append(list(map(int, input().split())))

        # find cell alone
        by_one = []
        for i in range(2):
            for j in range(rows):
                if all(get_neighbor_of_value(arr, i, j, op=o) + arr[i][j] > cap for o in get_args(CellOperator)):
                    by_one.append((i,j))

        # find cell with two neighbors
        by_two = []
        for i in range(2):
            for j in range(rows):
                if (i,j) in by_one:
                    continue

                if all 