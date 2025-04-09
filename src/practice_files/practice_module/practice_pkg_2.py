import importlib.util
import sys
import unittest


def main():
    spec = importlib.util.find_spec("practice_pkg.Cls")

    if spec:
        print("class Cls has loaded")
    else:
        print("No one loaded.")


if __name__ == "__main__":
    main()
