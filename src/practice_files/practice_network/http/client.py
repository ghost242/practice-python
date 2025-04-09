from multiprocessing import Process, Pool

import socket

import random

import time
import logging

from practice_files.practice_network.tcp import (
    create_tcp_sock,
    send_message,
    recv_message,
)

BUF_LEN = 1024


def client():
    host = ""
    port = random.randint(10000, 20000)

    print(f"Client - {port}")

    sock = create_tcp_sock(host, port)

    retry = 10
    while True:
        try:
            sock.connect(("127.0.0.1", 8080))
        except socket.TimeoutError as err:
            logging.error(f"socket timeout: {err}")
            if retry:
                retry -= 1
                time.sleep(0.3)
            else:
                return
        else:
            break

    send_message(sock, "Hello world!!" * 1234)

    msg = recv_message(sock)

    print(msg)

    sock.close()


def fund():
    print(random.randint(10000, 20000))

    time.sleep(1)

    print(random.randint(10000, 20000))


if __name__ == "__main__":
    ps = []
    for _ in range(10):
        print("Call fund")
        p = Process(target=client)
        p.start()
        ps.append(p)

    for p in ps:
        p.join()
