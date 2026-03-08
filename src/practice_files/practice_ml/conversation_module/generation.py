from __future__ import annotations

import logging

from practice_files.practice_ml.conversation_module.types import (
    AgentSpec,
    ConversationState,
)
from practice_files.practice_ml.conversation_module.prompts import (
    build_reply_messages,
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


async def generate_reply(agent: AgentSpec, state: ConversationState) -> str:
    """
    Use the agent's LLM to generate the next content message.

    Responsibilities:
    - Assumes the orchestrator (decision layer) has already chosen this agent
      to speak on the current turn.
    - Builds a reply prompt that defines HOW the agent should speak
      (persona, style, constraints) using build_reply_messages.
    - Calls agent.llm.ainvoke(messages) and normalizes the result to a string.

    Requirements on agent.llm:
    - Must support: await agent.llm.ainvoke(messages)
    - Should return either:
        - a dict with a 'content' field, or
        - an object with a .content attribute, or
        - a plain string
    """
    print(">> Generating reply for %s..." % agent.agent_id)

    messages = build_reply_messages(agent, state)
    result = await agent.llm.ainvoke(messages)

    if isinstance(result, dict):
        print(">> Generated result dict: %s" % result)
        content = result.get("content", "")
    else:
        print(">> Generated result other type: %s" % result)
        content = getattr(result, "content", str(result))

    return content.strip()
