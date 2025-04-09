from sentence import Sentence

if __name__ == "__main__":
    s = Sentence('"The time has come," the Walrus said,')

    for word in s:
        print(word)

    l = list(s)

    print(l)
