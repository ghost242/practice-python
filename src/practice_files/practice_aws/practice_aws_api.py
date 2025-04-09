import threading
from requests import Request, Session
import multiprocessing

from time import time


def send_data(index):
    print(f"Send message to api gateway for lambda: {index}")
    st = time()
    req = Request(
        method="POST",
        url="https://127.0.0.1",
        headers={
            "Connection": "Keep-Alive",
            "Keep-Alive": "timeout=5, max=10",
            "Content-Type": "plain/text",
            "X-Amz-Invocation-Type": "Event",
        },
        data=f"{index}: lambda runner",
    )
    pr = req.prepare()

    s = Session()

    resp = s.send(
        pr,
        timeout=5,
    )
    print(f"runtime: {time() - st}")
    print(resp.status_code, resp.reason)
    print(resp.content)


def run_sub_process():
    pass


def main():
    send_data(100)


def async_main():
    threads = []

    for i in range(1):
        threads.append(threading.Thread(target=send_data, args=(i,)))

    for t in threads:
        t.start()

    for t in threads:
        t.join()
    # p = multiprocessing.Process(target=run_sub_process)


if __name__ == "__main__":
    main()
