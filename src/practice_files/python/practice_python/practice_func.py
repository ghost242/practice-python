def func():
    def a():
        pass

    def b():
        pass

    def c():
        pass

    print(locals())


def main():
    print(globals())
    func()


if __name__ == "__main__":
    main()
