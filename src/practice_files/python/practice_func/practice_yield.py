"""
generator 함수의 yield를 try-except로 감싸고, 외부에서 이 함수를 호출하는 부분에서 Exception을 발생시키면 try-except가 영향을 주는지에 대한 테스트.
코드 테스트 결과 전혀 영향을 주지 않음.
"""


def func():
    value = 100
    try:
        yield value

        print("yielded value")
    except ValueError:
        print("Error raised: " + str(value))


def main():
    v = func()

    for i in v:
        print(i)

    raise ValueError("zxcv")


if __name__ == "__main__":
    main()
