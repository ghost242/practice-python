from types import TracebackType
from typing import Any
from contextlib import AbstractContextManager


class DummyDB(AbstractContextManager):
    def __init__(self) -> None:
        pass

    def __call__(self, *args: Any, **kwds: Any) -> Any:
        pass

    def __enter__(self) -> Any: ...

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> bool | None: ...
