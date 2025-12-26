class Cls:
    def __init__(self, name):
        self.__dict__["is_none"] = lambda v: v is None


class SystemException(Exception):
    exc_name: str

    def __init_subclass__(cls) -> None:
        cls.exc_name = cls.__name__.replace("Exception", "")
        print("init subclass")

        return super().__init_subclass__()


class NaverException(SystemException):
    pass


def main():
    # c = Cls("asdf")

    # setattr(c, "is_int", lambda v: isinstance(v, int))

    # print(c)
    # print(c.is_none(None))
    # print(c.is_int(10))
    try:
        raise NaverException("Test exception")
    except NaverException as e:
        print(e)


if __name__ == "__main__":
    main()
