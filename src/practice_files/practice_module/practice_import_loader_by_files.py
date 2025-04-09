import importlib
import os

files = os.listdir()

for f in files:
    if f == "practice_file_load.py":
        file_load = importlib.import_module(os.path.splitext(f)[0])
        if hasattr(file_load, "func"):
            # if "func" in list(dir(file_load)):
            file_load.func()
