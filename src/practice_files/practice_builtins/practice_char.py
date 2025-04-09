if __name__ == "__main__":
    # Intel cpu using little endian
    r = map(chr, list(range(ord("a"), ord("z"), 2)))

    print(list(r))
