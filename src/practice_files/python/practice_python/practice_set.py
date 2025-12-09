def main():
    s1 = {1, 2, 3}
    s2 = {2, 3, 4}
    s3 = {2, 3}

    # print(s1.difference(s2))
    # print(s2.difference(s1))
    print(s3.difference(s1))
    print(s1.difference(s3))
    print(bool(s3.difference(s1)))


if __name__ == "__main__":
    main()
