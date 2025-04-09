import os
import sys
import boto3
from functools import partial


# def get_formula(a, b):
#     return "{} * {} = {}".format(a, b, a * b)
#
#
# formula = partial(get_formula, int(input()))
# print("\n".join(list(map(formula, range(1, 10)))))
#
# print("---END---")

if __name__ == "__main__":
    # print(os.path.exists('/usr/lib'))
    import importlib.util

    print(sys.meta_path)
    print(os.listdir("/opt/python"))

    spec = importlib.util.find_spec("boto3")
    boto3 = spec.loader.load_module()
    print(spec.submodule_search_locations)
    print(sys.modules)
    print("boto3" in sys.modules)
    # print(dir(boto3))
