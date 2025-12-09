import sys
import logging


def add_functioncall_hook():
    def hook_func(event, data):
        print("==="*10)
        print(event, type(event), dir(event))
        print("~~~"*10)
        print(data, type(data), dir(data))
        for val in data:
            print(val, type(val), dir(val))
            print("---"*10)
        print("==="*10)
    sys.addaudithook(hook_func)

def callie_1(param1):
    logging.info("This is callie_1")
    logging.info(param1)

def callie_2(param2):
    logging.warning("This is callie_2")
    logging.warning(param2)


def main():
    logging.getLogger().setLevel(logging.INFO)

    callie_1('asdf')
    callie_2(1234)

if __name__ == "__main__":
    add_functioncall_hook()
    main()

