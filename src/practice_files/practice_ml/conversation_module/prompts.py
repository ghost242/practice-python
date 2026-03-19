from __future__ import annotations

from typing import Sequence

from practice_files.practice_ml.conversation_module.types import (
    AgentSpec,
    ConversationState,
    SubtopicPlan,
    Turn,
)

# ---------------------------------------------------------
# Global response constraints
# ---------------------------------------------------------

MAX_RESPONSE_TOKENS = 1000

RESPONSE_SIZE_RULE = (
    "Response size constraint:\n"
    f"- Maximum response length: about {MAX_RESPONSE_TOKENS} tokens.\n"
    "- Prefer concise statements rather than long explanations.\n"
    "- Avoid unnecessary repetition.\n"
)


# ---------------------------------------------------------
# Helpers
# ---------------------------------------------------------


def _format_recent_turns(state: ConversationState, limit: int = 20) -> str:
    if not state.turns:
        return "(none)"

    turns = state.turns[-limit:]
    lines: list[str] = []

    for turn in turns:
        participant = turn.participant_id
        text = (turn.content or "").strip()
        lines.append(f"{turn.turn_index}. {participant}: {text}")

    return "\n".join(lines)


def _format_turns(turns: Sequence[Turn]) -> str:
    if not turns:
        return "(none)"

    return "\n".join(
        f"{turn.turn_index}. {turn.participant_id}: {(turn.content or '').strip()}"
        for turn in turns
    )


def _format_agent_goals(agent: AgentSpec) -> str:
    if not agent.goal:
        return "(none)"
    return "\n".join(f"{i + 1}. {goal}" for i, goal in enumerate(agent.goal))


def _format_agent_traits(agent: AgentSpec) -> str:
    if not agent.traits:
        return "(none)"
    return "\n".join(f"- {trait}" for trait in agent.traits)


def _format_agent_base_knowledge(agent: AgentSpec) -> str:
    if not agent.base_knowledge:
        return "(none)"
    return "\n".join(f"- {item}" for item in agent.base_knowledge)


def _format_agent_summary(runtime) -> str:
    summary = (runtime.summary_text or "").strip()
    return summary or "(none)"


def _format_open_questions(agent: AgentSpec, state: ConversationState) -> str:
    runtime = state.get_participant_state(agent.participant_id)
    if not runtime.latest_open_questions:
        return "(none)"
    return "\n".join(f"- {item}" for item in runtime.latest_open_questions)


def _format_current_focus(agent: AgentSpec, state: ConversationState) -> str:
    runtime = state.get_participant_state(agent.participant_id)
    focus = (runtime.current_focus or "").strip()
    return focus or "(none)"


# ---------------------------------------------------------
# Reply generation
# ---------------------------------------------------------


def build_reply_messages(
    agent: AgentSpec,
    state: ConversationState,
) -> list[dict]:
    runtime = state.get_participant_state(agent.participant_id)

    history = _format_recent_turns(state, agent.max_history_turns)
    goals = _format_agent_goals(agent)
    traits = _format_agent_traits(agent)
    base_knowledge = _format_agent_base_knowledge(agent)
    summary = _format_agent_summary(runtime)
    open_questions = _format_open_questions(agent, state)
    current_focus = _format_current_focus(agent, state)

    current_subtopic = None
    if 0 <= state.current_subtopic_index < len(state.subtopics):
        current_subtopic = state.subtopics[state.current_subtopic_index]

    subtopic_title = (
        current_subtopic.title if current_subtopic else state.topic
    )
    subtopic_achievement = (
        current_subtopic.achievement if current_subtopic else state.achievement
    )

    system_prompt = (
        "You are participating in a structured technical discussion.\n"
        "Speak briefly and naturally like a person in a meeting.\n"
        "Use your role, traits, goals, background knowledge, and latest summary.\n"
        "Your goals are guidance for perspective and responsibility, not a checklist to report explicitly.\n"
        "Stay grounded in the current subtopic and discussion history.\n"
        "Do not write a document, outline, or markdown.\n\n"
        f"{RESPONSE_SIZE_RULE}\n"
        f"Role: {agent.role}\n"
        f"Traits:\n{traits}\n\n"
        f"Background knowledge:\n{base_knowledge}\n\n"
        "Output JSON only.\n"
        '{"reply":"your message","intent":"short reasoning"}'
    )

    user_prompt = (
        f"Session topic:\n{state.topic}\n\n"
        f"Session objective:\n{state.achievement}\n\n"
        f"Current subtopic:\n{subtopic_title}\n\n"
        f"Current subtopic achievement:\n{subtopic_achievement}\n\n"
        f"Your goals:\n{goals}\n\n"
        f"Your latest summary:\n{summary}\n\n"
        f"Your current focus:\n{current_focus}\n\n"
        f"Your open questions:\n{open_questions}\n\n"
        f"Conversation history:\n{history}\n\n"
        "Write your next reply."
    )

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]


# ---------------------------------------------------------
# Agent summary refresh
# ---------------------------------------------------------


def build_agent_summary_update_messages(
    agent: AgentSpec,
    state: ConversationState,
) -> list[dict]:
    runtime = state.get_participant_state(agent.participant_id)

    history = _format_recent_turns(state, agent.max_history_turns)
    goals = _format_agent_goals(agent)
    traits = _format_agent_traits(agent)
    base_knowledge = _format_agent_base_knowledge(agent)
    prior_summary = _format_agent_summary(runtime)
    open_questions = _format_open_questions(agent, state)
    current_focus = _format_current_focus(agent, state)

    current_subtopic = None
    if 0 <= state.current_subtopic_index < len(state.subtopics):
        current_subtopic = state.subtopics[state.current_subtopic_index]

    subtopic_title = (
        current_subtopic.title if current_subtopic else state.topic
    )
    subtopic_achievement = (
        current_subtopic.achievement if current_subtopic else state.achievement
    )

    system_prompt = (
        "You analyze a technical discussion transcript.\n"
        "Refresh only the specified agent's latest working summary.\n"
        "Use the agent's role, traits, goals, and background knowledge to interpret their contribution.\n"
        "Do not score or evaluate goals one by one.\n"
        "Do not evaluate other agents.\n"
        "Be conservative and use only evidence visible in the transcript.\n\n"
        f"{RESPONSE_SIZE_RULE}\n"
        "Return structured JSON only.\n\n"
        "{"
        '"summary":"short refreshed summary of the agent contribution and current position",'
        '"latest_open_questions":["question"],'
        '"current_focus":"optional focus area"'
        "}"
    )

    user_prompt = (
        f"Session topic:\n{state.topic}\n\n"
        f"Session objective:\n{state.achievement}\n\n"
        f"Current subtopic:\n{subtopic_title}\n\n"
        f"Current subtopic achievement:\n{subtopic_achievement}\n\n"
        f"Agent:\n{agent.display_name} ({agent.role})\n\n"
        f"Traits:\n{traits}\n\n"
        f"Background knowledge:\n{base_knowledge}\n\n"
        f"Agent goals:\n{goals}\n\n"
        f"Previous summary:\n{prior_summary}\n\n"
        f"Existing current focus:\n{current_focus}\n\n"
        f"Existing open questions:\n{open_questions}\n\n"
        f"Conversation history:\n{history}\n\n"
        "Refresh this agent's latest summary for future reply generation."
    )

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]


# ---------------------------------------------------------
# Subtopic conclusion
# ---------------------------------------------------------


def build_subtopic_conclusion_messages(
    *,
    state: ConversationState,
    current_subtopic: SubtopicPlan,
    subtopic_turns: Sequence[Turn],
) -> list[dict]:
    transcript = _format_turns(subtopic_turns)

    system_prompt = (
        "You are the host closing a technical discussion subtopic.\n"
        "Summarize only the current subtopic discussion.\n"
        "Write a concise conclusion that states:\n"
        "- what was clarified or decided\n"
        "- what remains unresolved if anything\n"
        "- how much the subtopic achievement was advanced\n\n"
        f"{RESPONSE_SIZE_RULE}\n"
        "Return JSON only.\n"
        '{"conclusion":"short subtopic conclusion"}'
    )

    user_prompt = (
        f"Session topic:\n{state.topic}\n\n"
        f"Current subtopic:\n{current_subtopic.title}\n\n"
        f"Current subtopic achievement:\n{current_subtopic.achievement}\n\n"
        f"Subtopic turns:\n{transcript}\n\n"
        "Produce the subtopic conclusion."
    )

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]


# ---------------------------------------------------------
# Final synthesis
# ---------------------------------------------------------


def _format_agent_contributions(
    state: ConversationState,
    agents: Sequence[AgentSpec],
) -> str:
    lines: list[str] = []

    for agent in agents:
        runtime = state.get_participant_state(agent.participant_id)

        summary = _format_agent_summary(runtime)
        goals = _format_agent_goals(agent)
        open_questions = _format_open_questions(agent, state)
        current_focus = _format_current_focus(agent, state)

        lines.append(f"{agent.display_name} ({agent.role})")
        lines.append("Goals:")
        lines.append(goals)
        lines.append("Latest summary:")
        lines.append(summary)
        lines.append("Current focus:")
        lines.append(current_focus)
        lines.append("Open questions:")
        lines.append(open_questions)
        lines.append("")

    return "\n".join(lines).strip()


def build_final_synthesis_messages(
    state: ConversationState,
    agents: Sequence[AgentSpec],
) -> list[dict]:
    history = _format_recent_turns(state, limit=max(50, len(state.turns)))
    contributions = _format_agent_contributions(state, agents)

    system_prompt = (
        "You are the host summarizing a multi-agent technical discussion.\n"
        "Synthesize key conclusions, unresolved questions, and next steps.\n\n"
        f"{RESPONSE_SIZE_RULE}\n"
        "Return JSON only.\n"
        '{"synthesis":"summary text","open_items":["item"],"next_steps":["step"]}'
    )

    user_prompt = (
        f"Discussion topic:\n{state.topic}\n\n"
        f"Session objective:\n{state.achievement}\n\n"
        f"Agent contributions:\n{contributions}\n\n"
        f"Full conversation:\n{history}\n\n"
        "Produce a final synthesis."
    )

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]
