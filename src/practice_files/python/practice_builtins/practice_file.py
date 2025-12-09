import os


print(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tests"))

print(__file__)
d = globals()

print(d)
