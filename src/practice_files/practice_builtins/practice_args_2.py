import sys


def main():
    args = sys.argv
    print(*[(i, v) for i, v in enumerate(args)])


if __name__ == "__main__":
    main()
