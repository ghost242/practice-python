"""
Time over
같은 로직으로 C99로 해결
"""
from typing import List

num_cases = int(input())
cases: List[List[int]] = []

for _ in range(num_cases):
    base, exp, *other = map(int, input().split())

    cases.append([base, exp])

for base, exp in cases:
    p = 1

    for _ in range(exp):
        p = p * base % 10
    
    print(p if p != 0 else 10)
