from abc import ABCMeta, ABC, abstractmethod
from typing_extensions import Self
from typing import Any


class Domain(metaclass=ABCMeta):
    def __new__(cls, **kwargs) -> Self:
        if cls == Domain:
            raise RuntimeError("Abstract Class cannot create instance.")
        else:
            o = super().__new__(cls)
            o.__dict__.update(kwargs)
            return o

    def __contains__(self, o):
        return isinstance(o, type(self))

    def __repr__(self) -> str:
        i = [f'{k}="{str(v)}"' for k, v in self.__dict__.items()]
        return f"<{type(self).__name__} {','.join(i)}>"


class Human(Domain):
    def __init__(self, name) -> None:
        super().__init__()
        self.name = name


if __name__ == "__main__":
    # d = Domain()
    d = Human(name="Socrates")
    print(d)
