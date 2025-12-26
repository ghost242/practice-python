import asyncio

from llama_index.llms.ollama.base import ChatMessage, MessageRole, ChatResponse
from llama_index.llms.ollama import Ollama


model_name = "gpt-oss:20b"

inst_a = Ollama(model_name, base_url="http://10.88.0.4:11434")


async def _resp_fn(message, *, history: list | None = None):
    if not history:
        history = []
    user_message = ChatMessage(
        content=message,
    )

    history.append(user_message)

    resp = inst_a.chat(messages=history)

    return resp.message


if __name__ == "__main__":
    answer = asyncio.run(_resp_fn("Could AI becomes friend to human?"))

    print(answer)
