import io
import socket

import logging


BUF_LEN = 1024


def create_tcp_sock(host: str, port: int) -> socket.socket:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((host, port))

    return sock


def recv_message(sock):
    msg = ""

    while True:
        _msg = sock.recv(BUF_LEN)
        logging.info(f"recv message({len(_msg)}): {_msg}")
        msg += _msg.decode()
        if len(_msg) < BUF_LEN:
            break

    return msg


def send_message(sock, message):
    buf = io.BytesIO(message.encode())

    sent = 0

    while True:
        _msg = buf.read(BUF_LEN)
        logging.info(f"send message({len(_msg)}): {_msg}")
        sock.send(_msg)
        sent += len(_msg)
        if len(_msg) < BUF_LEN:
            break

    return sent
