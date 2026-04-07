from __future__ import annotations

from typing import TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class LangChainStructuredRuntime:
    """
    LangChain-backed structured runtime for agents.

    This adapter accepts any LangChain chat model that supports
    `with_structured_output`.
    """

    def __init__(self, chat_model) -> None:
        self._chat_model = chat_model

    def invoke_structured(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        response_model: type[T],
    ) -> T:
        structured_llm = self._chat_model.with_structured_output(
            response_model
        )
        return structured_llm.invoke(
            [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ]
        )
