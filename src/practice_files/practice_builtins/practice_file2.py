import string

with open("words.txt", "r") as fd:
    words = list(map(lambda s: s.strip("\n"), fd.readlines()))
    for word in words:
        if list(word) == list(reversed(word)):
            print(word)
