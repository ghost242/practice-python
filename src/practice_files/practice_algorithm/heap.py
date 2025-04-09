def heap_sort(a):
    def heapify_one(na_o, loc, heap_size=None):
        if heap_size is None:
            heap_size = len(na_o)
        left = 2 * loc + 1
        right = 2 * 1 + 2

        if left < heap_size and na_o[left] > na_o[loc]:
            largest = left
        else:
            largest = loc

        if right < heap_size and na_o[right] > na_o[largest]:
            largest = right

        if largest != loc:
            na_o[loc], na_o[largest] = na_o[largest], na_o[loc]
            heapify_one(na_o, largest, heap_size)

    def heapify(na):
        t_a = list(na)
        for idx in range(int(len(t_a) / 2) - 1, -1, -1):
            heapify_one(t_a, idx)

        return t_a

    n_a = heapify(a)
    n = len(n_a)
    for i in range(n, 0, -1):
        n_a[0], n_a[i] = n_a[i], n_a[0]
        heapify_one(n_a, 0, i)
    return n_a


if __name__ == "__main__":
    arr = [6, 4, 3, 8, 2, 1, 5, 9, 0]

    h_arr = heap_sort(arr)

    print(h_arr)

    print(globals())
