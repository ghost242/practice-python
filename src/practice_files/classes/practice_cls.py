from dataclasses import dataclass
from typing import overload


@dataclass
class A:
    __slot__ = ("a", "b")

    def __init__(self):
        self.a = (10,)
        self.b = "b"


@dataclass
class B(A):
    __slot__ = ("__c", "d")

    def __init__(self):
        super().__init__()
        self.__c = 1.1
        self.d = 2 + 3j

    def get_members(self):
        return self.__slot__

    @property
    def c(self):
        return self.__c

    @c.setter
    def c(self, _):
        pass


class MySQLContext:
    @overload
    def __init__(self, info: dict):
        ...

    @overload
    def __init__(
        self,
        *,
        drivername="mysql+mysqlconnector",
        username,
        password,
        host,
        port,
        database,
        query=None,
    ):
        ...

    def __init__(
        self,
        info: dict = None,
        *,
        drivername="mysql+mysqlconnector",
        username=None,
        password=None,
        host=None,
        port=None,
        database=None,
        query=None,
    ):
        if info is None:
            info = dict()

        self.username = (info.get("user", None) or username,)
        self.password = (info.get("pwd", None) or password,)
        self.host = (info.get("host", None) or host,)
        self.port = (info.get("port", None) or port,)
        self.database = (info.get("db_name", None) or database,)

    def __repr__(self):
        return "MySQLContext<user:{},host:{},port:{},db_name:{}>".format(
            self.username, self.host, self.port, self.database
        )


if __name__ == "__main__":
    # b = B()
    #
    # print(b.__dict__)
    # print(B.__dict__)
    #
    # print(b.c)
    #
    # b.c = 1000
    #
    # print(b.c)

    print(A in B.mro())
