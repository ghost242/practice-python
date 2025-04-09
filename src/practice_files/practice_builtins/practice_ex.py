from datetime import datetime, timedelta


class TimeIterator:
    __slot__ = ("start", "end", "current", "delta")

    def __init__(self, start, end):
        self.start = datetime.min + timedelta(seconds=start)
        self.end = datetime.min + timedelta(seconds=end)
        self.current = datetime.min + timedelta(seconds=start)
        self.delta = timedelta(seconds=1)

    def __iter__(self):
        return self

    def __next__(self):
        try:
            if self.current >= self.end:
                raise StopIteration()
            return "{:0>2}:{:0>2}:{:0>2}".format(
                self.current.hour, self.current.minute, self.current.second
            )
        except StopIteration as e:
            raise e
        finally:
            self.current += self.delta

    def __getitem__(self, idx):
        t = self.start + timedelta(seconds=idx)
        return "{:0>2}:{:0>2}:{:0>2}".format(t.hour, t.minute, t.second)


def main():
    start, stop, index = (88234, 88237, 1)

    for i in TimeIterator(start, stop):
        print(i)

    print("\n", TimeIterator(start, stop)[index], sep="")


if __name__ == "__main__":
    main()
