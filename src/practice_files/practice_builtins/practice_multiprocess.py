import multiprocessing
from time import sleep


def func(n, store):
    print(n)
    store[n] = n * n


def main_practice_manager():
    for i in range(5):
        with multiprocessing.Manager() as manager:
            print(str(i) + "번째 실행")

            res_set = manager.dict()
            ps = [
                multiprocessing.Process(
                    target=func, name=f"prc_{n}", args=(n * i, res_set)
                )
                for n in range(20)
            ]

            for p in ps:
                p.start()

            for p in ps:
                p.join()

            print(res_set)


def wait_func(idx):
    for i in range(10):
        print(f"print out line_{idx}_{i}")
        sleep(1)


def main_practice_process():
    ps = []
    idx = 0
    while True:
        if input() == "q":
            break

        q = multiprocessing.Queue()

        p = multiprocessing.Process(target=wait_func, args=(idx,))
        idx += 1

        # p.run()

        p.start()
        p.join(2)

        ps.append(p)

    # for p in ps:
    #     p.join()


if __name__ == "__main__":
    main_practice_process()
