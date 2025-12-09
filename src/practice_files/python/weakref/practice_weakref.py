"""
weakref with dataclass

Practice to add attribute for reference type.
  - Not support the attribute type of ReferenceType for BaseModel, dataclass in pydantic
  - Available to add the attribute type of ReferenceType for dataclass(basic library)
"""
from weakref import ref, ReferenceType
# from pydantic import BaseModel, Field
# from pydantic.dataclasses import dataclass
from dataclasses import dataclass, field, asdict
from typing import Optional, Any, ForwardRef


@dataclass
class Object:
    field: str = field(default="", kw_only=True)

@dataclass
class SuperObject:
    obj: ReferenceType[Object]

o = Object(field="abc")
r = ref(o)

so = SuperObject(obj = ref(o))

print(so)
print(so.obj, so.obj())
print(id(so.obj()), id(o))

print(o.field, so.obj().field)

o.field = "xyz"
print(so.obj().field)
