import re
import reprlib


class Sentence:
    def __init__(self, text):
        self.text = text
        self.words = re.compile(r"\w+").findall(text)

    def __getitem__(self, index):
        print("__getitem__")
        return self.words[index]

    def __len__(self):
        print("__len__")
        return len(self.words)

    def __repr__(self):
        return "Sentence(%s)" % reprlib.repr(self.text)


class Sentence1:
    def __init__(self, text):
        self.text = text
        self.words = re.compile(r"\w+").findall(text)

    def __iter__(self):
        for word in self.words:
            yield word
        return

    def __repr__(self):
        return "Sentence1(%s)" % reprlib.repr(self.text)


class Sentence2:
    def __init__(self, text):
        self.text = text

    def __iter__(self):
        return (
            match.group() for match in re.compile(r"\w+").findall(self.text)
        )

    def __repr__(self):
        return "Sentence2(%s)" % reprlib.repr(self.text)
