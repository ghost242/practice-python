"""
Metaclass 에 대한 실험코드

MetaClass 클래스는 type을 상속받는 메타클래스 구조이고, 내부에 맴버변수를 가짐
Class는 MetaClass를 메타클래스로 갖는 클래스임.

클래스의 attribute로 메타클래스의 맴버를 가져올 수 있지만, 인스턴스는 메타클래스의 맴버를 가져올 수 없음.
인스턴스의 attribute로 클래스의 맴버를 가져올 수 있지만, 메타클래스의 맴버는 가져올 수 없음.
클래스의 classmethod 메소드에서는 init에서 정의된 맴버는 가져올 수 없지만 init 바깥에서 선언된 맴버는 가져올 수 있음.
init 바깥에서 선언되는 변수는 클래스 자체의 attribute로 사용하는 것이 적합할 것으로 생각됨.

메타클래스에서 선언된 함수는 classmethod처럼 첫번째 파라미터로 cls가 나옴.
동작은 classmethod처럼 동작하는데, classmethod처럼 객체 인스턴스가 호출할 수는 없음.
이 내부 파라미터의 cls는 repr은 메타클래스의 클래스 타입을 문자열 반환하지만 실제 타입은 메타클래스임.
그리고 cls는 메타클래스의 맴버에 접근할 수 있음.

메타클래스는 인스턴스를 만들 수 없음. type(name: str, bases: Tuple[type, ...], dict: Dict[str, Any])와 유사하게 동작함.
"""


class MetaClass(type):
    x = 10
    y = 20

    def meta_func(cls):
        print(cls)
        print(type(cls))
        print(cls.__name__)
        print(dir(cls))
        print(cls.x)
        print(cls.y)


class Class(metaclass=MetaClass):
    t = 100
    r = 200

    def __init__(self):
        self.a = "x"
        self.b = "y"

    def func(self):
        print(self.a)
        print(self.x)
        print(self.t)

    @classmethod
    def cfunc(cls):
        print(cls.x)
        print(cls.a)
        print(cls.t)


def main():
    print(type(type(Class)), type(Class), Class)
    print(type(Class) == MetaClass)
    # print(dir(Class))
    # print(Class.meta_func())
    # c = Class()
    #
    # Class.meta_func()
    # MetaClass.meta_func(Class)
    #
    # try:
    #     print('Class.x', Class.x)
    # except:
    #     pass
    #
    # try:
    #     print('Class.a', Class.a)
    # except:
    #     pass
    #
    # try:
    #     print('Class.t', Class.t)
    # except:
    #     pass
    #
    # try:
    #     print('c.x', c.x)
    # except:
    #     pass
    #
    # try:
    #     print('c.a', c.a)
    # except:
    #     pass
    #
    # try:
    #     print('c.t', c.t)
    # except:
    #     pass


if __name__ == "__main__":
    main()
