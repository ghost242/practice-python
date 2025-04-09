from warnings import warn
import sys
import os

from importlib.util import module_from_spec, spec_from_file_location


code = """
def func():
    print("this is sample function")
    
class Cls:
    a: int
    b: int
    c: int    
"""


def main():
    src_path = "./practice_raw_code.py"

    spec = spec_from_file_location("cls", src_path)
    for n in dir(spec):
        print(n, getattr(spec, n))

    if spec:
        module = module_from_spec(spec)
        spec.loader.exec_module(module)

        print(dir(module))

        c = module.cls()
        c.func()


if __name__ == "__main__":
    main()
    