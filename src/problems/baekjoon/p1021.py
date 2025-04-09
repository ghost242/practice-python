from copy import copy

def head(arr:list):
    return arr[0]


def pop(arr:list):
    x = arr[0]

    arr = arr[1:]
    return x, arr

def rshift(arr:list):
    x = arr[-1]
    arr = [x] + arr[:-1]

    return arr

def lshift(arr:list):
    x = arr[0]
    arr = arr[1:] + [x]

    return arr

def get_op_counts(a, t):
    op_count = 0
    x = 0

    while x != t:
        if head(a) == t:
            x, a = pop(a)
            break

        elif t< head(a):
            a = rshift(a)

            op_count += 1
        elif t> head(a):
            a = lshift(a)
            op_count += 1

    return op_count



def main(n, targets):
    a = list(range(1, n+1))

    op_count = 0

    while targets:
        min_oc = [None, 9999]
        for t in targets:
            oc = get_op_counts(a, t)

            if min_oc[1] > oc:
                min_oc[1] = oc
                min_oc[0] = t
        
                print(f"{min_oc=}")
        op_count += min_oc[1]
        targets.remove(min_oc[0])

    print(op_count)
    

if __name__ == "__main__":
    # n, *other = map(int, input().split())
    # targets = list(map(int, input().split()))

    n = 10
    targets = [2,9,5]

    main(n, targets)
