""" Sample for study about HTTP/1.1"""

import socket

import logging

from practice_files.practice_network.tcp import (
    create_tcp_sock,
    recv_message,
    send_message,
)


def main():
    try:
        serv = create_tcp_sock("", 8080)

        serv.listen()

        while True:
            cli, addr = serv.accept()
            logging.info(f"client address: {addr[0]}:{addr[1]}")

            msg = recv_message(cli)

            sending = send_message(cli, msg)

            print(msg, sending)
            cli.close()
    except socket.herror as e:
        errno, err_msg = e
        logging.error(f"socket error: {errno}, {err_msg}")
    except socket.timeout as e:
        logging.error(f"socket timeout: {e}")
    except Exception as e:
        logging.error(f"other exception: {e}")
    finally:
        serv.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    main()
