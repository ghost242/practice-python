from typing import overload, Optional
import json

class parent():
    def __init__(self, *args, x = 10):
        print("This is parent. ", x, args)

class child(parent):
    def __init__(self, *args, x = 20):
        super(child, self).__init__(*args)
        print("This is child. ", x)


def run():
    pass

if __name__ == "__main__":
    run()
