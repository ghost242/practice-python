def remove_item():
    l = ["a", "b", "c", "d", "e"]

    print(l)

    del l[l.index("c")]

    print(l)


def main():
    l1 = [1, 2, 3, 4]
    l2 = [3, 4, 5, 6]

    # 중복값을 보존함.
    print([*l1, *l2])

    l3 = ["a", "b", "c"]
    l4 = ["c", "d", "e"]

    # string도 마찬가지임.
    print([*l3, *l4])

    # set은 중복값을 허용하지 않기 때문에 유효함.
    print({*l1, *l2})


if __name__ == "__main__":
    remove_item()
