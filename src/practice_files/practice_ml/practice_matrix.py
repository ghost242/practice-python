from typing import TypeVar
from functools import singledispatch

Mat2d = TypeVar('Mat2d', list[list[int | float]])

def transpose(m: Mat2d) -> Mat2d:
    return [[m[j][i] for j in range(len(m[0]))] for i in range(len(m))]

@singledispatch
def matmul(m1: Mat2d, m2: Mat2d) -> Mat2d:
    return [
        [sum(a * b for a, b in zip(row, col)) for col in transpose(m2)]
        for row in m1
    ]

@singledispatch
def matmul(m1: int | float, m2: Mat2d) -> Mat2d:
    return [
        [a * m1 for a in row]
        for row in m2
    ]

def matsum(m1: Mat2d, m2: Mat2d) -> Mat2d:
    return [
        [a + b for a, b in zip(row, col)]
        for row, col in zip(m1, m2)
    ]

def matsub(m1: Mat2d, m2: Mat2d) -> Mat2d:
    return [
        [a - b for a, b in zip(row, col)]
        for row, col in zip(m1, m2)
    ]

def determinant(m: Mat2d) -> int | float:
    if len(m) == 2:
        return m[0][0] * m[1][1] - m[0][1] * m[1][0]
    return sum(
        (-1) ** (i + j) * m[0][j] * determinant(minor(m, i, j))
        for i in range(len(m))
        for j in range(len(m))
    )

def minor(m: Mat2d, i: int, j: int) -> Mat2d:
    return [row[:j] + row[j + 1:] for row in (m[:i] + m[i + 1:])]

def inverse(m: Mat2d) -> Mat2d:
    det = determinant(m)
    if det == 0:
        raise ValueError('Determinant is zero')
    return matmul(
        [
            [1 / det if i == j else 0 for i in range(len(m))]
            for j in range(len(m))
        ],
        transpose(minor(m, 0, 0))
    )
