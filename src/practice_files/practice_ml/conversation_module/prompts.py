from __future__ import annotations

import logging
from typing import List, Sequence

from practice_files.practice_ml.conversation_module.types import (
    AgentSpec,
    ConversationState,
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# ===== DECISION PROMPTS =====================================================


def build_decision_system_prompt(
    agents: Sequence[AgentSpec],
    state: ConversationState,
) -> str:
    """
    System prompt for the *coordinator* decision call.

    One LLM call decides SPEAK / WAIT / FINISH for every agent,
    based on their persona prompts and the latest conversation history.

    This prompt is written assuming the model is invoked in
    JSON / structured-output mode. The caller will parse the
    returned JSON object directly.
    """
    # Compact agent summary for small models
    agent_lines = []
    for a in agents:
        prompt_short = (
            (a.prompt[:160] + "...") if len(a.prompt) > 160 else a.prompt
        )
        agent_lines.append(
            f"- {a.agent_id}: role={a.role}; persona={prompt_short}"
        )

    agents_block = "\n".join(agent_lines)

    return (
        "You are a coordinator supervising a multi-agent technical discussion.\n"
        "You are invoked in structured-output / JSON mode. The caller will\n"
        "parse your reply as JSON and ignore any extra text.\n"
        "\n"
        "Your task: decide whether EACH agent should SPEAK, WAIT, or FINISH\n"
        "on the next turn.\n"
        "\n"
        "Return EXACTLY one JSON object with this schema:\n"
        "{\n"
        '  "decisions": [\n'
        "    {\n"
        '      "agent_id": "<id>",\n'
        '      "action": "SPEAK" | "WAIT" | "FINISH",\n'
        '      "score": <number in [0.0, 1.0]>,\n'
        '      "intent": "<short phrase>"\n'
        "    },\n"
        "    ... one entry for EVERY agent listed below, in any order ...\n"
        "  ]\n"
        "}\n"
        "\n"
        "Meaning of actions (per agent):\n"
        "- SPEAK  : should talk on the next turn; can add NEW, useful,\n"
        "           persona-consistent content toward the Goal.\n"
        "- WAIT   : should stay silent on the next turn, but remains in the\n"
        "           discussion and may SPEAK on later turns.\n"
        "- FINISH : this agent is personally done with this session. They have\n"
        "           no more meaningful contributions and will leave permanently.\n"
        "\n"
        "Decision rules (apply independently to each agent):\n"
        "- Consider ONLY what that agent can add, given their role and persona prompt.\n"
        "- If the latest message mentions @<agent_id>, that agent should prefer\n"
        "  SPEAK if they can respond with useful, relevant content.\n"
        "- An agent may SPEAK again even if they spoke last turn, but only if\n"
        "  their previous answer is clearly incomplete and they must continue.\n"
        "- If an agent spoke last turn and is not explicitly mentioned now,\n"
        "  they should usually WAIT unless clarification is obviously needed.\n"
        "- Use FINISH only when it is clear that this agent personally has no\n"
        "  more valuable contributions for the entire session.\n"
        "- Do NOT use FINISH just because the group is close to the Goal; it is\n"
        "  about that specific agent leaving, not stopping the group.\n"
        "- If unsure between SPEAK and WAIT, prefer the option that improves\n"
        "  the discussion, but avoid FINISH when uncertain.\n"
        "\n"
        "Field constraints:\n"
        "- You MUST output one decision object for EVERY agent listed below.\n"
        '- When action == "WAIT", set score = 0.0.\n'
        '- When action == "SPEAK" or "FINISH", set score in [0.0, 1.0] to\n'
        "  reflect your confidence that this is the correct action.\n"
        '- Keep "intent" under 12 words, focused on the main idea of what the\n'
        "  agent would say (for SPEAK) or why they are done (for FINISH).\n"
        "- Do NOT include any extra keys.\n"
        "- Do NOT wrap the JSON in backticks or markdown fences.\n"
        "\n"
        "Agents:\n"
        f"{agents_block}\n"
        "\n"
        "Additional inputs:\n"
        "- The user message will include the latest message from each agent (may be empty).\n"
        "  Use this to avoid asking an agent to repeat themselves and to judge continuation.\n"
        "\n"
        "Discussion context:\n"
        f"- Topic: {state.topic}\n"
        f"- Goal: {state.achievement}\n"
    )


def build_decision_messages(
    agents: Sequence[AgentSpec],
    state: ConversationState,
) -> List[dict]:
    """
    Build messages for the coordinator decision call.

    The model is expected to return ONLY a JSON object matching the schema
    in the system prompt. The caller may also enforce this via structured
    output / JSON mode at the API level.
    """
    print(">> Building decision messages for %s agents" % len(agents))

    system_prompt = build_decision_system_prompt(agents, state)
    # Use the max per-agent history limit; decisions may need a bit more context.
    max_hist = max(a.max_history_turns for a in agents) if agents else 15
    history = state.turns[-max_hist:]

    # Latest message per agent (default empty string)
    latest_by_agent = {a.agent_id: "" for a in agents}
    for t in reversed(state.turns):
        if (
            t.speaker_type == "agent"
            and t.speaker_id in latest_by_agent
            and not latest_by_agent[t.speaker_id]
        ):
            latest_by_agent[t.speaker_id] = t.content
        if all(latest_by_agent.values()):
            break

    latest_block_lines = []
    for a in agents:
        msg = (latest_by_agent.get(a.agent_id) or "").strip()
        msg_short = (msg[:220] + "...") if len(msg) > 220 else msg
        latest_block_lines.append(f"- {a.agent_id}: {msg_short}")
    latest_block = "\n".join(latest_block_lines)

    history_str = ""
    for t in history:
        history_str += f"{t.speaker_id}: {t.content}\n"

    user_msg = (
        "Latest message by agent (may be empty):\n"
        f"{latest_block}\n\n"
        "Here is the recent conversation (most recent at the end):\n"
        f"{history_str}\n"
        'Now return ONLY the JSON object with the "decisions" array for all\n'
        "agents, following the schema described in the system message.\n"
    )

    print(
        ">> Built decision messages for %s: system prompt length=%d, user prompt length=%d"
        % (len(agents), len(system_prompt), len(user_msg))
    )
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_msg},
    ]


# ===== META-DECISION PROMPTS ===============================================


def build_meta_system_prompt(state: ConversationState) -> str:
    """
    System prompt for the meta decision (REFRESH or CLOSE).

    This is also designed for JSON / structured-output mode.
    """
    return (
        "You are a coordinator supervising a multi-agent technical discussion.\n"
        "Right now, no agent wants to speak: they all chose WAIT or FINISH.\n"
        "You must decide whether to:\n"
        "- REFRESH: propose a new subtopic, angle, or next step that can help\n"
        "           achieve the Goal of this discussion, or\n"
        "- CLOSE  : decide that additional conversation is unnecessary.\n"
        "\n"
        "You are invoked in structured-output / JSON mode. The caller will\n"
        "parse your reply directly as JSON.\n"
        "\n"
        "Return EXACTLY one JSON object with this schema:\n"
        "{\n"
        '  "action": "REFRESH" | "CLOSE",\n'
        '  "subtopic": "<short phrase if action == REFRESH, else empty string>",\n'
        '  "intent": "<short reason, under 12 words>"\n'
        "}\n"
        "\n"
        "Constraints:\n"
        '- When action == "CLOSE", set "subtopic" to "" (empty string).\n'
        '- "intent" should briefly explain WHY you chose REFRESH or CLOSE.\n'
        "- Do NOT add extra keys or text outside the JSON object.\n"
        "- Do NOT wrap the JSON in backticks or markdown.\n"
        "\n"
        "Discussion context:\n"
        f"- Topic: {state.topic}\n"
        f"- Goal: {state.achievement}\n"
        "\n"
        "Recent discussion follows:\n"
    )


def build_meta_messages(state: ConversationState) -> List[dict]:
    system_prompt = build_meta_system_prompt(state)
    history = state.turns[-10:]

    history_str = ""
    for t in history:
        history_str += f"{t.speaker_id}: {t.content}\n"

    user_msg = (
        history_str
        + "\nBased on this, choose REFRESH or CLOSE and output ONLY the JSON\n"
        "meta decision object as specified in the system message.\n"
    )

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_msg},
    ]


# ===== REPLY PROMPTS (unchanged, plain-text) ===============================


def build_reply_system_prompt(
    agent: AgentSpec, state: ConversationState
) -> str:
    """
    System prompt for content generation only.
    It defines how the agent should speak, but NOT when.
    Orchestration (SPEAK/WAIT/FINISH, continuation, speaker picking)
    is handled only by the decision prompt and the controller.
    """
    return (
        f"You are {agent.agent_id}, a {agent.role}, in a multi-agent technical discussion.\n"
        "Write only your own message, from your own perspective.\n"
        "Rules:\n"
        f"- Speak only as {agent.agent_id}; do not write dialogue for anyone else.\n"
        "- Do not prefix your text with any speaker labels (no 'name:').\n"
        "- Stay reactive to the recent messages; do not restart the topic from scratch.\n"
        "- Be concise, technical, and concrete.\n"
        "- Avoid repeating points that were already made.\n"
        "- Maximum 5 sentences (about 120 words).\n\n"
        f"Persona instructions:\n{agent.prompt}\n\n"
        f"Topic:\n{state.topic}\n"
        f"Goal:\n{state.achievement}\n"
    )


def build_reply_messages(
    agent: AgentSpec, state: ConversationState
) -> List[dict]:
    """
    Build messages for the reply (content) generation.
    This function is only about WHAT the agent should say,
    assuming the orchestrator already decided that this agent speaks now.
    """
    print(">> Building reply messages for %s..." % agent.agent_id)

    system_prompt = build_reply_system_prompt(agent, state)

    # For small models, keep history short to reduce token load.
    history = state.turns[-5:]

    history_lines = []
    for t in history:
        history_lines.append(f"{t.speaker_id}: {t.content}")

    user_msg = (
        "Recent discussion:\n" + "\n".join(history_lines) + "\n\n"
        "Now write your next message, following the rules."
    )

    print(
        ">> Built reply messages for %s: system prompt length=%d, user prompt length=%d"
        % (agent.agent_id, len(system_prompt), len(user_msg))
    )
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_msg},
    ]
