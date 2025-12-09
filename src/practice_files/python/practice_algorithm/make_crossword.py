import random


def scan_word(word):
    # does not exists any word
    pass


def set_word(board, coord, word):
    # failed that board is full
    # set board
    pass


def add_word(board, words):
    try:
        word = random.choice(words)
    except IndexError:
        return board
    else:
        coord = scan_word(word)

        if coord is None:
            pass

        new_board = set_word(board, coord, word)

        del words[words.index(word)]

        add_word(new_board, words)


def main():
    input_words = []
    board = [[0 for __ in range(20)] for _ in range(20)]
    add_word(board, input_words)


if __name__ == "__main__":
    main()
