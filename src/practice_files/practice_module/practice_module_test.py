import importlib.util
from importlib import import_module

from practice_files.practice_module_name import func, Cls
import sys


def to_class(class_full_name: str):
    *module_name, class_name = class_full_name.split(".")
    module = import_module(".".join(module_name))

    return getattr(module, class_name)


def main():
    print(sys.path)

    # cls = to_class("practice_files.practice_import.NewClass")
    package = import_module(".practice_cls", "practice_files.classes")
    cls = getattr(package, "B")
    c = cls()

    print(c)


if __name__ == "__main__":
    main()
