import dataclasses


def func(val):
    print(id(val), id(val.a), id(val.b), id(val.c))

    val.a = "cvweqte"
    val.b = 1.213455
    val.c = 123 + 483j
    print(val.a, val.b, val.c)


import pickle


def conv_func(item):
    ret = dict()
    for k, v in item:
        ret[k] = pickle.dumps(v)
    return ret


# from dataclasses import dataclass, asdict, fields, field


@dataclasses.dataclass
class DataClassType:
    sub_1: int
    sub_2: int


@dataclasses.dataclass
class DataClassA:
    mem_1: int  # int 타입 맴버변수
    mem_2: float  # float 타입 맴버변수
    mem_3: DataClassType  # 임의로 만든 타입 맴버변수
    mem_4: str = dataclasses.field(
        default="default"
    )  # 기본 값이 "default"로 정의된 str 타입 맴버변수
    mem_5: list = dataclasses.field(
        default_factory=list
    )  # 해당 타입의 기본 객체를 만드는 함수가 정의된 list 타입 맴버변수


def main():
    # 새로운 DataClassA 객체 생성
    dc = DataClassA(10, 10.2, DataClassType(1, 2), "abcd")

    #
    print(dc)

    print(dataclasses.fields(dc))
    print(dataclasses.asdict(dc))


if __name__ == "__main__":
    main()
