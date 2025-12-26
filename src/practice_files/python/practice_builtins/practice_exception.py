import os
import sys
import traceback
import logging
import pickle
import binascii

from pathlib import Path
from tblib import pickling_support


pickling_support.install()


def find_parent(target_parent):
    cur = Path(os.getcwd())

    while cur != cur.root:
        if (cur / target_parent).exists():
            return cur / target_parent
        else:
            cur = cur.parent
    else:
        raise FileNotFoundError(f"Not found {target_parent} in {os.getcwd()}.")


def exc_hook(
    tp,
    val,
    tb,
):
    print(tb)
    stacks = traceback.extract_tb(tb)
    for stack in stacks:
        stack.filename = stack.filename.replace(
            str(project_root), "<PROJECT_ROOT>"
        )


sys.excepthook = exc_hook


project_root = find_parent("codelab-python")


def a():
    raise ValueError("raised error")


def aa():
    a()


def aaa():
    aa()


def b():
    try:
        aaa()
    except Exception as e:
        # Exception에서 traceback은 pickling이 불가능한 객체임. 이유로인해 pickling에 실패함.
        tb_obj = binascii.hexlify(pickle.dumps(e.__traceback__))

        return tb_obj
    # a()


def c():
    # try:
    #     exc_origin = b()
    # except Exception as e:
    #     fg = traceback.walk_tb(e.__traceback__)
    #     ss = traceback.StackSummary.extract(fg)

    #     print(ss)
    #     print("---" * 9)
    #     for frame in fg:
    #         print(frame)

    #     raise e

    tb_origin = b()
    tb = pickle.loads(binascii.unhexlify(tb_origin))
    # print(traceback.format_exception(type(exc), exc, exc.__traceback__))
    # print(id(exc), type(exc), exc)
    # fg = traceback.walk_tb(exc.__traceback__)
    # print("---Frames START---")
    # for frame in fg:
    #     print(frame)
    # print("---Frames END---")
    raise Exception().with_traceback(tb)


def l():
    raise OSError("error")


def m():
    raise KeyError("error")


def n():
    raise FileNotFoundError("error")


def main_exc(func):
    try:
        func()
    except Exception as e:
        # l.exception(str(e), exc_info=e)
        # exc_type, exc_value, exc_traceback = sys.exc_info()

        tb = e.__traceback__
        for k in dir(tb.tb_frame):
            if k in ["f_builtins", "f_globals"] or k.startswith("__"):
                continue
            print(k, getattr(tb.tb_frame, k))

        while tb.tb_next is not None:
            tb = tb.tb_next

        # print(type(exc_type), exc_type)
        # print(type(exc_value), exc_value)
        # print(type(exc_traceback), exc_traceback)


def finally_test():
    try:
        # raise Exception("hello")
        c()

        # print("hello")
    except Exception as e:
        # print(traceback.format_exception(type(e), e, e.__traceback__))
        print(e.__traceback__)

        raise e
    finally:
        print("called finally")


# def sender(conn):
#     try:
#         print("call c")
#         c()
#     except Exception as e:
#         print("exception raised")
#         conn.send(binascii.hexlify(pickle.dumps(e.__traceback__)))
#         conn.close()

# def receiver(conn):
#     start = time.time()
#     try:
#         resp = conn.recv()
#         tb = pickle.loads(binascii.unhexlify(resp))
#         raise Exception().with_traceback(tb)
#     except Exception as e:
#         print(traceback.format_exception(type(e), e, e.__traceback__))


def main():
    ###
    # messenger on single process
    finally_test()

    ###
    # messenger on multi process
    # send, receive = multiprocessing.Pipe()
    # ps = [
    #     multiprocessing.Process(target=receiver, args=(receive, )),
    #     multiprocessing.Process(target=sender, args=(send, ))
    # ]

    # for p in ps:
    #     print(p, "start")
    #     p.start()

    # for p in ps:
    #     print(p, "join")
    #     p.join()


if __name__ == "__main__":
    main_exc(l)
    main_exc(m)
    main_exc(n)
    # main()
