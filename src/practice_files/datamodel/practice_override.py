"""
practice the model property on pydantic
The pydantic checks validation type of properties in model class from BaseModel
And sub model can override type of properties for same property on super class
"""

from pydantic import BaseModel


class sup_model(BaseModel):
    a: int
    b: str


class sub_model(sup_model):
    a: list[int]
    b: dict[str, str]


class sub_2_model(sup_model):
    a: list[int] | int
    b: dict[str, str] | str


# success case
res = sup_model.model_validate({"a": 10, "b": "asdf"})
print(res)

res = sub_model.model_validate(
    {"a": [1, 2, 3, 4], "b": {"x": "qwer", "y": "zcv"}}
)
print(res)

res = sub_2_model.model_validate(
    {
        "a": 10,  # list[int]
        "b": "asdf",  # dict[str, str]
    }
)
print(res)
res = sub_2_model.model_validate(
    {"a": [1, 2, 3, 4], "b": {"x": "qwer", "y": "zcv"}}
)
print(res)

# failure case
res = sub_model.model_validate(
    {
        "a": 10,  # list[int]
        "b": "asdf",  # dict[str, str]
    }
)
print(res)
