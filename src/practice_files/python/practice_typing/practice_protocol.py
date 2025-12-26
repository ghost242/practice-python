from typing import TypeVar, Protocol

T = TypeVar["T"]


class cls:
    x: tp

    def method_a(self, t: tp) -> tp:
        self.x = t
        return self.x
