"""
find sorting index

>>> 8
>>> [4,1,6,1,3,6,1,4]
<<< 4 0 6 1 3 7 2 5
"""
from copy import copy

def sort(arr):
    i = 0
    sorted_arr = copy(arr)
    while i < (len(sorted_arr) - 1):
        if sorted_arr[i] > sorted_arr[i+1]:
            sorted_arr[i], sorted_arr[i+1] = sorted_arr[i+1], sorted_arr[i]
            i = 0
        else:
            i += 1

    return sorted_arr

def find_index(a, b):
    indexes =[]
    for i in range(len(a)):
        idx = b.index(a[i])
        
        indexes.append(idx)
        b[idx] = -1
    
    return indexes

if __name__ == "__main__":
    A = [4,1,6,1,3,6,1,4]
    B = sort(A)

    print(*find_index(A,B))
