from dataclasses import dataclass, field, Field, fields, MISSING

from practice_builtins.practice_dataclass_conversion import MetaDataClass

"""
참고:
    https://docs.python.org/3.7/library/functions.html#exec
"""

# There is two other versions.
# 1. if default or default_factory is exists, then this field is set a kwarg.
# class decorator
def with_keyword_args(cls):
    if getattr(cls, "__init__", None) is None:
        return

    params = "self, "
    cls_fields = cls.__dataclass_fields__
    args = []
    kwargs = []
    init_body = []
    for _, f in cls_fields.items():
        if f.default_factory != MISSING and f.default != MISSING:
            raise Exception(
                "Must be set only one of parameter(default or default_factory)"
            )
        elif f.default_factory != MISSING:
            kwargs.append((f.name, f.type, f.default_factory()))
        elif f.default != MISSING:
            kwargs.append((f.name, f.type, f.default))
        else:
            args.append((f.name, f.type))

    params += ",".join([f"{arg[0]}:{arg[1].__name__}" for arg in args]) + ","
    if kwargs:
        params += "*," + ",".join(
            [
                f"{kwarg[0]}:{kwarg[1].__name__} = {kwarg[2]}"
                for kwarg in kwargs
            ]
        )

    for arg in args:
        init_body.append(f"    self.{arg[0]} = {arg[0]}")
    for kwarg in kwargs:
        init_body.append(f"    self.{kwarg[0]} = {kwarg[0]}")

    init_header = f"def __init__({params}):\n"

    __init_fn = init_header + "\n".join(init_body)

    gl = {}
    ns = {}
    exec(__init_fn, gl, ns)

    setattr(cls, "__init__", ns["__init__"])

    return cls


@with_keyword_args
@dataclass(init=False)
class kwcls(metaclass=MetaDataClass):
    a: int = field(default=100)
    b: str = field()


def kwdc_t1():
    print(kwcls("abc"))


@dataclass()
class cls(metaclass=MetaDataClass):
    a: int = field(default=100)
    b: str = field()


def kwdc_t2():
    print(kwcls("abc"))


# 2. if parameter(kwarg) is True, then this field is set a kwarg.


def field_kw(
    *,
    default=MISSING,
    default_factory=MISSING,
    init=True,
    repr=True,
    hash=None,
    compare=True,
    metadata=None,
    kwarg=False,
):
    pass


class FieldKw(Field):
    def __init__(
        self,
        default,
        default_factory,
        init,
        repr,
        hash,
        compare,
        metadata,
        kwarg,
    ):
        super().__init__(
            default, default_factory, init, repr, hash, compare, metadata
        )
        self.kwarg = kwarg

    def __repr__(self):
        return super().__repr__()

    def __set_name__(self, owner, name):
        super().__set_name__(owner, name)


def main():
    kwdc_t1()
    kwdc_t2()


if __name__ == "__main__":
    main()
