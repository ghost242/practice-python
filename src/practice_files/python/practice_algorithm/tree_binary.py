from dataclasses import dataclass, field
from typing import Any
from typing import Optional


@dataclass
class Node:
    parent: Optional["Node"] = field(default=None)
    children: tuple["Node", "Node"] = field(default_factory=tuple)
    value: Any = field(default=None)

class BinaryTree:
    def __init__(self, root: Node):
        self.root = root
    
    def insert(self, parent: Node, value: Any):
        
        pass

    def delete(self, value: Any):
        pass

    def search(self, value: Any):
        pass
