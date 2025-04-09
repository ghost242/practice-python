import dataclasses
import enum
import functools
import json
import logging

import typing
from datetime import date, datetime
from urllib.parse import ParseResult, urlunparse


def to_dict(inst: typing.Any):
    """

    :param inst:
    :return:
    """

    def object_type_converter(value):
        """
        work for unsupported type about JSON

        :param value: Any value for convert
        :return: object for JSON validated type
        """
        if dataclasses.is_dataclass(value):
            ret = dataclasses.asdict(value, dict_factory=to_dict)
        elif isinstance(value, datetime):
            ret = value.strftime("%Y-%m-%dT%H:%M:%S%z")
        elif isinstance(value, date):
            ret = value.strftime("%Y-%m-%d")
        elif issubclass(type(value), enum.Enum):
            ret = value.value
        elif isinstance(value, ParseResult):
            ret = urlunparse(value)
        elif not isinstance(value, str) and isinstance(value, typing.Sequence):
            ret = [object_type_converter(val) for val in value]
        elif isinstance(value, dict):
            ret = {
                str(key): object_type_converter(val)
                for key, val in value.items()
            }
        else:
            ret = value
        return ret

    res_dict: dict = dict()
    for k, v in inst:
        if v is not None:
            res_dict[k] = object_type_converter(v)

    return res_dict


def custom_type_caster(target_type, val):
    # if target_type == datetime:
    #     try:
    #         ret = str_to_datetime(val)
    #     except ValueError:
    #         try:
    #             ret = str_to_datetime(val, dt_format=DEFAULT_DATE_FORMAT)
    #         except ValueError:
    #             ret = val
    # elif target_type == timedelta:
    #     ret = timedelta(float(val))
    # else:
    #     raise TypeError("Unknown Type")
    #
    # return ret
    return val


class MetaDataClass(type):
    __primitive_type = (complex, float, int, bool, str)
    __sequential_type = (
        list,
        set,
        tuple,
    )
    __mapper_type = (dict,)

    def from_dict(
        cls,
        arg: dict,
        *,
        key_mapper: typing.Callable[
            [typing.KeysView], typing.Sequence[str]
        ] = None,
    ):
        """
        dataclass 패키지에서 asdict 함수에 대응하는 함수를 작성하기 위해 추가한 함수.
        class method로 만들기 위해 metaclass에 정의하였으므로 class의 metaclass로
        이 클래스를 할당하는 것으로 사용할 수 있다.
        dataclass가 아닌 class에 적용하는 경우에 오류가 발생할 수 있다.(Field 객체를 중심으로 동작하기 때문)

        ex)
        @dataclass
        class cls(metaclass=MetaDataClass):
            param1: str
            param2: int

        >> inst = cls.from_dict(dict(param1="hello", param2=100))
        cls("hello", 100)

        :param arg: Dataclass로 객체화 하기위해 할당하는 값
        :type arg: dict
        :param key_mapper: arg 파라미터의 각 key 값이 dataclass의 field 값을 맵핑하기 위한
        값. None인 경우에는 반드시 key값과 일치하는 field 만을 대응시키는 동작을 기본으로 함.
        :type key_mapper: Callable[[typing.KeysView], typing.Sequence[str]]
        :return: 해당 클래스의 객체.
        :raises KeyError: arg 객체가 갖고있는 키와 dataclass의 field간에 키가 일치하지 않는 경우
        :raises ValueError: arg 객체의 value가 지정한 정의된 타입으로 전환되지 않고, default_factory도 지정되지 않아서 타입캐스팅이 되지 않는 경우
        :raises TypeError: arg 객체의 value가 dataclass의 field에 지정된 타입으로 타입캐스팅이 되지 않는 경우
        """

        def __type_cast_seq(seq_type: typing.Type, val: typing.Any):
            if hasattr(seq_type, "__args__"):
                """
                sequence type의 경우 __args__ 변수에 들어오는 값이 반드시 1개임.
                둘 이상 들어오는 경우에는 오류.
                """
                item_types = getattr(seq_type, "__args__")[0]
                type_ = getattr(seq_type, "__origin__")
            else:
                item_types = str
                type_ = seq_type

            if isinstance(val, str):
                return type_(
                    map(
                        lambda i: __type_caster(item_types, i.strip()),
                        val.split(","),
                    )
                )
            else:
                return type_(map(lambda i: __type_caster(item_types, i), v))

        def __type_cast_dict(map_type: typing.Type, val: typing.Any):
            if hasattr(map_type, "__args__"):
                key_type, value_type = getattr(map_type, "__args__")
                type_ = getattr(map_type, "__origin__")
            else:
                key_type, value_type = (str, str)
                type_ = map_type
            caster = __type_caster
            if value_type == typing.Any:
                caster = lambda t_, i_: i_

            if type_ == dict:
                if isinstance(val, str):
                    try:
                        conv_target = json.loads(val,)
                    except json.JSONDecodeError:
                        conv_target = val
                elif isinstance(val, dict):
                    conv_target = val
                else:
                    raise TypeError(
                        f"Value type is not mapper type"
                        f"(target: {type_}, value type: {type(val)}, value: {val})"
                    )
                ret = type_(
                    [
                        (key_, caster(value_type, val))
                        for key_, val in conv_target.items()
                    ]
                )
            else:
                if not isinstance(val, dict):
                    raise TypeError(
                        f"Value type is not mapper type"
                        f"(target: {type_}, value type: {type(val)}, value: {val})"
                    )
                ret = type_(
                    [
                        (key_, caster(value_type, val))
                        for key_, val in val.items()
                    ]
                )

            return ret

        def __type_caster(
            field_type: typing.Type,
            value: typing.Any,
            default_factory: typing.Callable[[typing.Any], typing.Any] = None,
        ):
            logging.debug(value)
            logging.debug(str(field_type))
            logging.debug(str(type(field_type)))
            if (
                hasattr(field_type, "__origin__")
                and getattr(field_type, "__origin__") == typing.Union
            ):
                cast_types = getattr(field_type, "__args__")
            else:
                cast_types = (field_type,)

            for cast_type in cast_types:
                if hasattr(cast_type, "__origin__"):
                    type_comp_src = getattr(cast_type, "__origin__")
                else:
                    type_comp_src = cast_type

                try:
                    if type_comp_src is bool:
                        result = value.lower() == "true"
                    elif type_comp_src in cls.__primitive_type:
                        result = cast_type(value)
                    elif type_comp_src in cls.__sequential_type:
                        result = __type_cast_seq(cast_type, value)
                    elif type_comp_src in cls.__mapper_type:
                        result = __type_cast_dict(cast_type, value)
                    elif (
                        isinstance(type_comp_src, typing.TypeVar)
                        or type_comp_src == typing.Any
                    ):
                        result = value
                    elif isinstance(type_comp_src, MetaDataClass):
                        result = type_comp_src.from_dict(
                            value, key_mapper=key_mapper
                        )
                    else:
                        result = custom_type_caster(type_comp_src, value)
                except TypeError:
                    logging.debug(f"{value} is not accepted type of {f.name}")
                    continue
                except KeyError as e:
                    logging.debug(
                        f"{f.name} is not exists in argument or {str(e)}"
                    )
                    continue
                except Exception as e:
                    logging.error(f"Common error: {str(e)}", exc_info=True)
                    raise e
                else:
                    break
            else:
                if callable(default_factory):
                    result = default_factory(value)
                else:
                    raise ValueError(
                        f"{f.name}({value}) cannot cast any types."
                    )
            return result

        def __default_setter(data_field):
            if all(
                [
                    data_field.default == dataclasses.MISSING,
                    data_field.default_factory == dataclasses.MISSING,
                ]
            ):
                raise ValueError(
                    f"Must set default or default_factory. field: {data_field.name}"
                )
            elif not data_field.default == dataclasses.MISSING:
                result = data_field.default
            elif not data_field.default_factory == dataclasses.MISSING:
                result = data_field.default_factory()
            else:
                raise ValueError(
                    "Neither set all of default and default_factory"
                )
            return result

        if not isinstance(arg, dict):
            raise TypeError("Type of arg is not dict")
        kv = dict()
        fs = dataclasses.fields(cls)

        if key_mapper:
            key_set = dict(zip(key_mapper(arg.keys()), arg.keys()))
        else:
            key_set = dict(zip(arg.keys(), arg.keys()))

        # init True, default not set, default_factory not set
        required_fields_name = {
            f.name
            for f in fs
            # init is False
            # -> when call __init__ function, this field is not parameterize
            if f.init
            and (
                # has not default or default_factory
                f.default == dataclasses.MISSING
                and f.default_factory == dataclasses.MISSING
            )
        }

        fs = {f for f in fs if f.init}

        if required_fields_name - set(key_set.keys()):
            raise TypeError(
                f"Not matched mapper key set and dataclass fields set:\n"
                f"[{required_fields_name=}]\n"
                f"[compared_fields_name={set(key_set.keys())}]"
            )

        for f in fs:
            key = key_set.get(f.name, None)
            v = arg.get(key, None)

            if f.name in arg and v is None:
                casted_value = v
            else:
                if f.name in key_set:
                    casted_value = __type_caster(f.type, v)
                else:
                    casted_value = __default_setter(f)
            kv[f.name] = casted_value
        return cls(**kv)

    def get_keys(cls):
        if dataclasses.is_dataclass(cls):
            return [k.name for k in dataclasses.fields(cls)]
        else:
            raise KeyError("This class is not dataclass type")


class CustomCls:
    a = 0
    b = ()
    c = 2

    def __init__(self, val):
        self.a, *self.b, self.c = val.split(",")

    def __str__(self):
        return f"a: {self.a}, b: {self.b}, c: {self.c}"

    def __repr__(self):
        return f"<class CustomCls | {str(self)}>"


@dataclasses.dataclass
class data(metaclass=MetaDataClass):
    a: int = dataclasses.field(default=0)
    b: int = dataclasses.field(default_factory=int)
    c: str = dataclasses.field(default_factory=str)
    d: list = dataclasses.field(default_factory=list)
    e: tuple = dataclasses.field(default=(0,))
    f: set = dataclasses.field(default_factory=set)
    g: dict = dataclasses.field(default_factory=dict)
    h: float = dataclasses.field(default_factory=float)
    i: complex = dataclasses.field(default_factory=complex)
    j: typing.Dict[typing.Text, typing.Text] = dataclasses.field(
        default_factory=dict
    )
    l: typing.Union[str, int, dict] = dataclasses.field(default=0)
    n: typing.List[float] = dataclasses.field(default_factory=list)
    t: CustomCls = dataclasses.field(
        default_factory=functools.partial(CustomCls, "10, 20, 30, 40")
    )

    def get_fields(self):
        # print(vars(self))
        fs = dataclasses.fields(self)
        print(*fs, sep="\n")


@dataclasses.dataclass
class MasterClass(metaclass=MetaDataClass):
    @dataclasses.dataclass
    class SubClass:
        a: str
        b: str
        c: str

    x: int
    y: SubClass
    z: SubClass


class meta_cls(type):
    def func(cls):
        print(vars(cls))
        print(*dataclasses.fields(cls), sep="\n")
        # print(c.cf())
        # print(c.sf())
        # print(c.val)


@dataclasses.dataclass
class c(metaclass=meta_cls):
    b: int
    _x: tuple = dataclasses.field(default_factory=tuple, init=False)

    def __post_init__(self):
        if len(self._x) > 0:
            print(self._x)
            print(self.t)

    @classmethod
    def cf(cls):
        return cls._x

    @staticmethod
    def sf():
        return [1, 2, 3, 4]

    @property
    def val(self):
        return "asdf"

    @classmethod
    def __prepare__(metacls, name, bases):
        print("__prepare__ | ", metacls, name, bases)
        metacls.func()


@dataclasses.dataclass
class sub_c(c):
    _x: tuple = (1, 2, 3)
    t: int = 100


def vannila_run():
    @dataclasses.dataclass
    class SampleDC(metaclass=MetaDataClass):
        a: int = dataclasses.field(default=0)
        b: int = dataclasses.field(default_factory=int)
        c: str = dataclasses.field(default_factory=str)
        d: list = dataclasses.field(default_factory=list)
        e: tuple = dataclasses.field(default=(0,))
        f: set = dataclasses.field(default_factory=set)
        g: dict = dataclasses.field(default_factory=dict)
        h: float = dataclasses.field(default_factory=float)
        i: complex = dataclasses.field(default_factory=complex)
        j: typing.Dict[typing.Text, typing.Text] = dataclasses.field(
            default_factory=dict
        )
        l: typing.Union[str, int, dict] = dataclasses.field(default=0)
        n: typing.List[float] = dataclasses.field(default_factory=list)
        t: CustomCls = dataclasses.field(
            default_factory=functools.partial(CustomCls, "10, 20, 30, 40")
        )

        def get_fields(self):
            fs = dataclasses.fields(self)
            print(*fs, sep="\n")

    r = {
        "d": "1,2,3,4,5",
        "h": "123.456",
        "a": "200",
        "e": "wer,tqrt,wert,w",
        "n": "1.123, 5, 12312",
        "i": "12+34j",
        "f": "rtyue,re,s,xvc,2345",
        "c": "sadf",
        "g": "a:x,b:y,c:z",
        "j": "u:1.23, v:2.34, w:3.45, x: 4.56, y: 5.67, z: 6.78",
        "l": "asdf",
    }
    r_dc = SampleDC.from_dict(r)

    print(r_dc)


def main():
    # c = cls()
    # c.b = 20
    # print(c)
    # c.func()
    # sub_c.func()
    # s = sub_c(1)

    # print(s._x)
    # n = sub_c(100)
    # print(n.val)
    # d = data(10, 20, 30)
    # e = data(100, 200, 300)
    # d = data()
    # e = data()

    # data.a = 1
    # data.b = 2
    # data.c = 3
    #
    # print(d)
    # print(e)
    #
    # print(id(10))
    # print(id(d.a))

    # raw = dataclasses.asdict(r_dc, dict_factory=conv_func)
    # print(raw)
    #
    # print(data.get_keys())

    # print(d)
    # print(repr(d))
    # d.get_fields()
    # print(vars(data))
    # print(data.__annotations__)
    # data_fields = fields(d)
    #
    # # print(getattr(d, data_fields[0]))
    # print(getattr(d, data_fields[0].name))
    # print(vars(d)[data_fields[0].name])
    #
    # cls = MasterClass(
    #     1, MasterClass.SubClass("1", "2", "3"), MasterClass.SubClass("t", "r", "s")
    # )
    #
    # v = {'x': 10, 'y': {'a': 'zxcv', 'b': 'qewr', 'c': 'gtw'}, 'z':{'a': 'zxcv', 'b': 'qewr', 'c': 'gtw'}}
    # cls = MasterClass(
    #     **v
    # )
    # print(cls)
    # print(repr(cls))
    # print(dataclasses.asdict(cls))
    # FlowUnit.from_dict()
    # print(dataclasses.is_dataclass(MasterClass))
    # print(isinstance(MasterClass, MetaDataClass))
    # print(hasattr(MasterClass, "from_dict"))
    pass


if __name__ == "__main__":
    # main()
    vannila_run()
