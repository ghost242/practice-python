import time


def func():
    for _ in range(10):
        print("Wait...")
        time.sleep(1)

    raise Exception("Test Exception")


if __name__ == "__main__":
    func()
