if __name__ == "__main__":
    val = "100\uc138\uc554\ubcf4\ud5d8_\uc11c\ube0c\ub9c1\ud06c_\ub2e4\uc774\ub809\ud2b8\uc0c1\ub2f4_pc"

    print(val)
    print("".join(list(map(str, val))))
    print("".join(list(map(str, val))).encode().decode())
    print("".join(list(map(lambda v: chr(ord(v)), val))))
    print("".join(list(map(lambda v: chr(ord(v)), val))).encode().decode())

    with open("test.txt", "w") as fd:
        fd.write(val + "\n")
        fd.write("".join(list(map(str, val))) + "\n")
        fd.write("".join(list(map(str, val))).encode().decode() + "\n")
        fd.write("".join(list(map(lambda v: chr(ord(v)), val))) + "\n")
        fd.write(
            "".join(list(map(lambda v: chr(ord(v)), val))).encode().decode()
            + "\n"
        )

    with open("test2.txt", "wb") as fd:
        fd.write(bytes(val.encode()))
