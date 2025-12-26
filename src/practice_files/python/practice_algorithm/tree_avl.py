from typing import Any
from dataclasses import dataclass, field


@dataclass
class Node:
    parent: "Node" = field()
    l_child: "Node"
    r_child: "Node"
    value: Any


class bst:
    root: Node

    def search(self, value):
        target = self.root

        while not (target.l_child is None and target.r_child is None):
            if target.value > value:
                target = target.l_child
            elif target.value < value:
                target = target.r_child
        else:
            return None

        return target

    def traversal(self):
        pass

    def insert(self, value):
        pass

    def delete(self, value):
        pass


class AVLTree:
    root: Node

    @staticmethod
    def balanced_factor(x: Node):
        pass
