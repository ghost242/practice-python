"""
object serialize using pickle
"""

from tblib import pickling_support
import pickle
import binascii
import traceback


pickling_support.install()

def func():
    raise Exception("Hello!")

def send_exception_by_str() -> str:
    """
    exception serialize
    """
    try:
        func()
    except Exception as e:
        print(traceback.StackSummary.extract(traceback.walk_tb(e.__traceback__)))
        print(e.__traceback__, type(e.__traceback__), hasattr(e.__traceback__, "__iter__"))
        print(e.__cause__, type(e.__cause__), hasattr(e.__cause__, "__iter__"))
        obj = pickle.dumps(e)
        hex_obj = binascii.hexlify(obj).decode()

        # print("Pickling exception with hex string: ", hex_obj)
        
        return hex_obj
    else:
        return ""


def receive_exception(exc_obj):
    """
    exception deserialize
    """
    
    # print(exc_obj)

    bytes_obj = binascii.unhexlify(exc_obj.encode())
    
    # print(bytes_obj)

    exc = pickle.loads(bytes_obj)
    msg = traceback.format_exception(exc)
    print(traceback.StackSummary.extract(traceback.walk_tb(exc.__traceback__)))
    print(exc.__traceback__, type(exc.__traceback__), hasattr(exc.__traceback__, "__iter__"))
    print(exc.__cause__, type(exc.__cause__), hasattr(exc.__cause__, "__iter__"))
    # print(type(exc), str(exc))
    print(*msg, sep='\n')

if __name__=="__main__": 
    print("< Raise exception and send by str")
    res = send_exception_by_str()
    print("> Receive exception and print")
    receive_exception(res)
