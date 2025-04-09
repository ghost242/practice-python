from time import time 
import logging
from tools.clocker import clocker

from random import choices, sample

def dist(a: list, b: list):
    d = 0
    for i, j in zip(a, b):
        if i != j:
            d += 1
    return d

def rev_arr(arr: list, idx_a, idx_b) -> list:
    return arr[:idx_a] + list(reversed(arr[idx_a:idx_b+1])) + arr[idx_b+1:]

not_found = 99999
visited = []
cap = 99999
call_counts: int 

# @clocker
def solver(src: list, dst: list, called: int, ):
    global cap
    global call_counts

    indent = "| " * called
    if cap < called:
        logging.debug(f"{indent}Capped({cap}) in called({called})!")
        return 99999
    call_counts += 1

    logging.debug(f"{indent}Call solver: {src=}, {dst=}, {called=}, {cap=}" )
    d_org = dist(src, dst)
    d_comp = len(src)
    
    dist_cache = {} 

    for i in range(len(src)):
        for j in (range(i+1, len(src))):
            tmp_arr = rev_arr(src, i, j)

            d_comp = dist(tmp_arr, dst)
            logging.debug(f"{indent}With {tmp_arr=} to {dst=}, {d_comp=}, {d_org=} when {i=}, {j=}")

            if d_comp == 0:
                logging.debug(f"{indent}Found in {called} times!")
                cap = called if cap > called else cap
                return called
            elif tmp_arr not in visited and d_org >= d_comp:
                dist_cache[tuple(tmp_arr)] = d_comp
            else:
                continue

    min_cache = min(dist_cache.values())
    dist_cache = {k: v for k, v in dist_cache.items() if v == min_cache}
    logging.debug(f"{min_cache=}, {dist_cache=}")
 
    dists = [99999]
    for cached in dist_cache.keys():
        if cached not in visited:
            visited.append(cached)
            dists.append(solver(list(cached), dst, called+1, ))
            visited.pop()

    logging.debug(f"{indent}Return min of {dists=}")
    return min(dists)


if __name__ == "__main__":
    logging.basicConfig(level=logging.WARNING)
    # start = input()
    # end = input()

    for _ in range(100):
        call_counts = 0
        cap = 99999
        start = choices("01", k=20)
        end = sample(start, k=len(start))
        print(f"start: {''.join(start)}", f"end: {''.join(end)}", sep="\n")

        l_start = list(int(c) for c in start)
        l_end = list(int(c) for c in end)

        if sum(l_start) != sum(l_end):
            print(-1)
        elif l_start == l_end:
            print(0)
        else:
            t0 = time()
            cnt = solver(l_start, l_end, 1)
            elapsed = time() - t0
            if elapsed > 2:
                print("time over; elapsed:", time() - t0, " call_counts:", call_counts)
           
            print(cnt)
