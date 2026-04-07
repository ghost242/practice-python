from __future__ import annotations

from typing import Protocol, TypeVar, runtime_checkable

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


@runtime_checkable
class StructuredAgentRuntime(Protocol):
    """
    General runtime interface for agent-style structured inference.

    This interface abstracts provider-specific model invocation away from
    host and participant agent implementations.
    """

    def invoke_structured(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        response_model: type[T],
    ) -> T:
        """
        Invoke the underlying model and parse the response as structured output.
        """
        ...
