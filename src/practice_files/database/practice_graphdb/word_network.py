from typing import Optional, Any, ForwardRef

import networkx as nx
from enum import StrEnum, auto
from pydantic import BaseModel, Field, PrivateAttr

from weakref import ReferenceType, ref


class NodeType(StrEnum):
    TYPE_A = auto()
    TYPE_B = auto()


class Node(BaseModel):
    __slots__ = ("__weakref__",)

    text: str = Field(default="")
    type: NodeType = Field(...)
    metadata: dict[str, Any] = Field(default_factory=dict)


class Relationship(BaseModel):
    from_node: Optional[Node] = Field(None)
    to_node: Optional[Node] = Field(None)
    relationship: str = Field(default="")


def runner():
    group_a = [
        Node(text="NodeA", type=NodeType.TYPE_A),
        Node(text="NodeB", type=NodeType.TYPE_A),
    ]

    group_b = [
        Node(text="NodeC", type=NodeType.TYPE_B),
        Node(text="NodeD", type=NodeType.TYPE_B),
    ]

    relations = [
        Relationship(
            from_node=group_b[0], to_node=group_a[0], relationship="rel_a"
        ),
        Relationship(
            from_node=group_b[0], to_node=group_a[1], relationship="rel_a"
        ),
        Relationship(
            from_node=group_b[1], to_node=group_a[0], relationship="rel_a"
        ),
        Relationship(
            from_node=group_b[1], to_node=group_a[1], relationship="rel_a"
        ),
        Relationship(
            from_node=group_b[0], to_node=group_b[1], relationship="rel_b"
        ),
        Relationship(
            from_node=group_a[0], to_node=group_a[1], relationship="rel_c"
        ),
    ]

    print(id(group_b[0]), "->", id(relations[0].from_node))
    print(group_b[0] == relations[0].from_node)

    graph = nx.DiGraph()

    for item_a in group_a:
        graph.add_node(
            item_a.text,
            **item_a.model_dump(
                exclude={
                    "text",
                }
            ),
        )
    for industry in group_b:
        graph.add_node(
            industry.text,
            **industry.model_dump(
                exclude={
                    "text",
                }
            ),
        )

    for relation in relations:
        graph.add_edge(
            relation.from_node().text,
            relation.to_node().text,
            relation.model_dump(include={"relationship"}),
        )

    print(nx.to_dict_of_dicts(graph))


class SuperModel(BaseModel):
    ref_sub: ReferenceType["SubModel"] | None = PrivateAttr(default=None)


class SubModel(BaseModel):
    value: int


def runner():
    sub = SubModel(value=10)

    sup = SuperModel(ref_sub=ref(sub))

    print(sup.ref_sub)


if __name__ == "__main__":
    runner()
