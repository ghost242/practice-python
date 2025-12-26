"""
Class inheritance example.
"""

import json


class GrandParent(dict):
    def __init__(self, hint):
        self.me = "Hello"

        for k, v in hint.items():
            self[k] = v


class Parent1(GrandParent):
    def __init__(self, hint):
        GrandParent.__init__(self, hint)

        print("grand_parent id: ", id(GrandParent))
        print("super id: ", id(super()))


class Parent2(GrandParent):
    def __init__(self, hint):
        GrandParent.__init__(self, hint)

        print("grand_parent id: ", id(GrandParent))
        print("super id: ", id(super()))

        self.me_too = "Dear"


class SiblingA(Parent2):
    """
    This class's `__init__` method has no problem.
    """

    def __init__(self, hint):
        print("[SiblingA]")
        Parent2.__init__(self, hint)

    def __repr__(self):
        return json.dumps(list(dir(self)))


class SiblingB(Parent2):
    """
    In `__init__` method,
        `super(Parent2, self).__init__(hint)` does not call Parent's `__init__`.
        `super().__init__(hint)` call Parent's `__init__`.

    But commonly, called `__init__` in GrandParent.
    """

    def __init__(self, hint):
        print("[SiblingB]")
        # super(Parent2, self).__init__(hint)
        super().__init__(hint)

    def __repr__(self):
        return json.dumps(list(dir(self)))


if __name__ == "__main__":
    a = SiblingA({"x": 10})
    b = SiblingB({"y": 20})

    print("a: ", repr(a))
    print("b: ", repr(b))

    # res;10
    print("a: ", a["x"])
    # res;20
    print("b: ", b["y"])

    # res;'y'
    try:
        print("a: ", a["y"])

    except Exception as e:
        print("a: ", str(e))

    # res;'x'
    try:
        print("b: ", b["x"])

    except Exception as e:
        print("b: ", str(e))

    # res;'type' object is not subscriptable
    try:
        print("a: ", SiblingA["x"])

    except Exception as e:
        print("a: ", str(e))

    # res;'type' object is not subscriptable
    try:
        print("b: ", SiblingB["y"])

    except Exception as e:
        print("b: ", str(e))

    print("a: ", a.me)
    print("b: ", b.me)

    print("a: ", a.me_too)
    print("b: ", b.me_too)
