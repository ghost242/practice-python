import argparse
import logging

from typing import List


class node:
    __name: str
    __children: List["node"]

    def __init__(self, name, children=None):
        self.__name = name
        if children is not None:
            self.__children = children

    def append_child(self, node):
        self.children.append(node)

    def remove_child(self, node):
        self.children.remove(node)

    def has_child(self, node):
        return node in self.children

    @property
    def name(self):
        return self.__name

    @property
    def children(self):
        return self.__children


def add_node(this: node, child: node):
    this.append_child(child)
    return this


def remove_node(this: node, target: node):
    if not this.has_child(target):
        return None
    else:
        this.remove_child(target)


def get_node(name: str, root: node):
    target = None
    if root.name == name:
        target = root
    else:
        for n in root.children:
            if n.name == name:
                target = n
            else:
                target = get_node(name, n)

    return target


def new_node(name: str):
    return node(name)


def show_node(root: node, depth: int = 0):
    _indent = "> "
    print(root.name)

    for n in root.children:
        print(_indent * depth, n.name)
        show_node(n, depth + 1)


def command_shell():
    root_parser = argparse.ArgumentParser(prog="simple_graph")

    subparsers = root_parser.add_subparsers(title="command")

    get_command = subparsers.add_parser("get")
    add_command = subparsers.add_parser("add")
    remove_command = subparsers.add_parser("remove")
    show_command = subparsers.add_parser("show")
    exit_command = subparsers.add_parser("exit")

    get_command.add_argument("name")
    add_command.add_argument("name")
    add_command.add_argument("parent_name")
    remove_command.add_argument("name")
    remove_command.add_argument("parent_name")
    show_command.add_argument("name")

    while True:
        cmd = input(">> ")
        logging.debug("command: %s (%d): %s", str(type(cmd)), len(cmd), cmd)

        parse_res = root_parser.parse_args(cmd.split(" "))

        logging.debug("parsed: %s: %s", parse_res, type(parse_res))

        if parse_res.command == "exit":
            print("Good bye!")
            break

        print(parse_res.command)


if __name__ == "__main__":
    logging.getLogger().setLevel(logging.DEBUG)

    command_shell()
