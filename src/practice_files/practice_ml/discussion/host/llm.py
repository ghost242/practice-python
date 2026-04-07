from __future__ import annotations

from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class HostLlmInterface:
    """
    Abstract LLM invocation boundary for host decisions.

    This isolates LangChain and provider-specific model clients from the host
    behavior contract.
    """

    def invoke_structured(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        response_model: type[T],
    ) -> T:
        raise NotImplementedError
