def main():
    l = [
        {"a": 10, "b": 20},
        {"a": "zxcv", "b": 20.123},
        {"a": 10112, "b": 323420},
        {"a": 10236, "b": "234dkjfnkadnf20"},
    ]

    # d = dict(tuple(j.items() for j in i for i in l))
    # print(d)
    print({f"({a}, {b})" for a in range(0, 10) for b in range(10, 20)})


if __name__ == "__main__":
    main()
