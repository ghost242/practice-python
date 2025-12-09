"""
typing.cast 

Practice for typing.cast to try type casting for instance to child class.
Actually, it does not works. `cast` should be read for semantic word, declaration.
"""
from typing import cast


class ACls:
    x: int
    y: int
    z: int

    def __init__(self, x=0, y=1, z=2) -> None:
        self.x = x
        self.y = y
        self.z = z
    
    def __str__(self):
        return f"<class {self.__class__.__name__} " + " ".join([f"{k}={v}" for k,v in self.__dict__.items() if not k.startswith("_")]) +">"
    
class BCls(ACls):
    a: str
    b: str
    c: str

    def __init__(self, a="a", b="b", c="c", *, x=0, y=1, z=2):
        super().__init__(x, y, z)
        self.a = a
        self.b = b
        self.c = c


def runner():
    a = ACls(1,2,3)

    print(type(a), a)  # <class '__main__.ACls'> <class ACls x=1 y=2 z=3>

    b = cast(BCls, a)  # Just declare type to BCls for variable `a`. It does not means of really converting to BCls.

    print(type(b), b)  # <class '__main__.ACls'> <class ACls x=1 y=2 z=3>


if __name__ == "__main__":
    runner()
