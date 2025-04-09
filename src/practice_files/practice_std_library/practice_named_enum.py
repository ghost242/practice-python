import enum
from typing import List, Any


class AutoCls(enum.Enum):
    def _generate_next_value_(name, start, count, last_values):
        return name


class EnumCls(AutoCls):
    apple = enum.auto()
    ball = enum.auto()
    cat = enum.auto()
    duck = enum.auto()

    def __str__(self):
        return ",".join([v for v in self._member_names_])


if __name__ == "__main__":
    print(str(EnumCls))
    a = EnumCls.apple
    print(str(a))
