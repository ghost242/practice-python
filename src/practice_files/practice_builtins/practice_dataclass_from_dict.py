import dataclasses
import functools
import logging
import math
import pickle
import typing
from dataclasses import _MISSING_TYPE, fields, is_dataclass
from datetime import date, datetime
from datetime import timedelta
from enum import Enum
from typing import Any, Sequence, Type, TypeVar


class MetaDataClass(type):
    def from_dict(cls, arg: dict):
        def __type_caster(cast_types: Sequence[Type], value: str):
            primitive_type = [complex, float, int, bool, str]
            sequential_type = (
                list,
                set,
                tuple,
            )
            mapper_type = (dict,)

            def __type_cast_seq(seq_type: Type, v: str):
                if hasattr(seq_type, "__args__") and hasattr(
                    seq_type, "__origin__"
                ):
                    item_type = getattr(seq_type, "__args__")[0]
                    type_ = getattr(seq_type, "__origin__")
                else:
                    item_type = str
                    type_ = seq_type
                return type_(
                    map(
                        lambda i: __type_caster([item_type], i.strip()),
                        v.split(","),
                    )
                )

            def __type_cast_mapper(map_type: Type, v: str):
                if hasattr(map_type, "__args__") and hasattr(
                    map_type, "__origin__"
                ):
                    key_type, value_type = getattr(map_type, "__args__")
                    type_ = getattr(map_type, "__origin__")
                else:
                    key_type, value_type = (str, str)
                    type_ = map_type
                caster = __type_caster
                if value_type == Any:
                    caster = lambda i: i
                # tokens = [token.strip().split(":") for token in v.split(",")]
                # raw_values = [(key, caster([value_type], val)) for key, val in tokens]
                # return type_(raw_values)

                return type_(
                    [
                        (key.strip(), caster([value_type], val.strip()))
                        for key, val in [
                            token.strip().split(":") for token in v.split(",")
                        ]
                    ]
                )

            for cast_type in cast_types:
                if hasattr(cast_type, "__origin__"):
                    type_comp_src = getattr(cast_type, "__origin__")
                else:
                    type_comp_src = cast_type

                try:
                    if type_comp_src is bool:
                        result = value.lower() == "true"
                    elif type_comp_src in primitive_type:
                        result = cast_type(value)
                    elif type_comp_src in sequential_type:
                        result = __type_cast_seq(cast_type, value)
                    elif type_comp_src in mapper_type:
                        result = __type_cast_mapper(cast_type, value)
                    elif isinstance(cast_type, TypeVar):
                        result = value
                    else:
                        raise TypeError("Unknown Type")
                except TypeError:
                    continue
                except KeyError as e:
                    logging.warning(
                        f"{f.name} is not exists in argument or {str(e)}"
                    )
                else:
                    break
            else:
                if callable(f.default_factory):
                    result = f.default_factory(value)
                else:
                    raise ValueError(
                        f"{f.name}({value}) cannot cast any types."
                    )
            return result

        def __default_setter(data_field):
            if all(
                [
                    isinstance(data_field.default, _MISSING_TYPE),
                    isinstance(data_field.default_factory, _MISSING_TYPE),
                ]
            ):
                raise ValueError("Must set default or default_factory")
            elif not isinstance(data_field.default, _MISSING_TYPE):
                result = data_field.default
            elif not isinstance(data_field.default_factory, _MISSING_TYPE):
                result = data_field.default_factory()
            else:
                raise ValueError(
                    "Neither set all of default and default_factory"
                )
            return result

        kv = dict()
        for f in fields(cls):
            if f.name in arg.keys():
                casted_value = __type_caster((f.type,), arg[f.name])
            else:
                casted_value = __default_setter(f)

            kv[f.name] = casted_value
        return cls(**kv)

    def get_keys(cls):
        if is_dataclass(cls):
            return [k.name for k in fields(cls)]
        else:
            raise Exception("This class is not dataclass type")


def dict_convert(items):
    ret = dict()
    for k, v in items:
        if isinstance(v, Exception):
            ret[k] = pickle.dumps(v)
        elif isinstance(v, date):
            if isinstance(v, datetime):
                ret[k] = v.strftime("%Y-%m-%dT%h:%M:%s%Z")
            else:
                ret[k] = v.strftime("%Y-%m-%d")

        elif isinstance(v, timedelta):
            val = v.days * 86400 + v.seconds
            mic = v.microseconds / (10 ** int(math.log10(v.microseconds)) + 1)
            ret[k] = val + mic
        elif isinstance(v, Enum):
            ret[k] = v.value
        else:
            raise TypeError("not JSON serializable : ", type(v))


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


if __name__ == "__main__":
    # main()
    vannila_run()
