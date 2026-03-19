from __future__ import annotations

from typing import Any, Optional, Sequence

from practice_files.practice_ml.conversation_module.llm_utils import (
    extract_llm_payload,
)
from practice_files.practice_ml.conversation_module.prompts import (
    RESPONSE_SIZE_RULE,
    build_subtopic_conclusion_messages,
)
from practice_files.practice_ml.conversation_module.types import (
    AgentSpec,
    ConversationState,
    DiscussionParticipant,
    SubtopicPlan,
    Turn,
)


def _default_subtopic_id(title: str, index: int) -> str:
    normalized = "".join(
        ch.lower() if ch.isalnum() else "-" for ch in (title or "").strip()
    )
    normalized = "-".join(part for part in normalized.split("-") if part)
    if not normalized:
        normalized = f"subtopic-{index + 1}"
    return normalized


def _coerce_subtopic_plans(
    raw_subtopics: Any,
    *,
    topic: str,
    achievement: str,
) -> list[SubtopicPlan]:
    if not isinstance(raw_subtopics, list):
        return []

    results: list[SubtopicPlan] = []

    for index, item in enumerate(raw_subtopics):
        if not isinstance(item, dict):
            continue

        title = str(item.get("title", "") or "").strip()
        kickoff_message = str(item.get("kickoff_message", "") or "").strip()
        sub_achievement = str(item.get("achievement", "") or "").strip()

        if not title:
            continue

        if not kickoff_message:
            kickoff_message = f"Discuss the subtopic '{title}' and move it toward resolution."

        if not sub_achievement:
            sub_achievement = achievement or topic

        subtopic_id = str(item.get("subtopic_id", "") or "").strip()
        if not subtopic_id:
            subtopic_id = _default_subtopic_id(title, index)

        results.append(
            SubtopicPlan(
                subtopic_id=subtopic_id,
                title=title,
                kickoff_message=kickoff_message,
                achievement=sub_achievement,
                conclusion="",
                status="PENDING",
            )
        )

    return results


def _fallback_subtopics(
    *,
    topic: str,
    achievement: str,
) -> list[SubtopicPlan]:
    return [
        SubtopicPlan(
            subtopic_id="topic",
            title=topic,
            kickoff_message=(
                f"Discuss this topic and move toward the session objective: {achievement}"
            ),
            achievement=achievement,
            conclusion="",
            status="PENDING",
        )
    ]


def _format_recent_turns(state: ConversationState, limit: int = 16) -> str:
    if not state.turns:
        return "(none)"

    turns = state.turns[-limit:]
    return "\n".join(
        f"{turn.turn_index}. @{turn.participant_id}: {turn.content}"
        for turn in turns
    )


def _format_agent_runtime(agent: AgentSpec, state: ConversationState) -> str:
    runtime = state.get_participant_state(agent.participant_id)

    return (
        f"id: {agent.participant_id}\n"
        f"name: {agent.display_name}\n"
        f"role: {agent.role}\n"
        f"goals: {agent.goal}\n"
        f"summary_text: {runtime.summary_text or '(none)'}\n"
        f"latest_open_questions: {runtime.latest_open_questions or '(none)'}\n"
        f"current_focus: {runtime.current_focus or '(none)'}\n"
        f"times_spoken: {runtime.times_spoken}\n"
        f"last_spoken_turn_index: {runtime.last_spoken_turn_index}"
    )


def _fallback_speaker(
    agents: Sequence[AgentSpec],
    state: ConversationState,
) -> AgentSpec | None:
    if not agents:
        return None

    ranked = sorted(
        agents,
        key=lambda agent: (
            state.get_participant_state(agent.participant_id).times_spoken,
            agent.participant_id,
        ),
    )
    return ranked[0]


def _get_current_subtopic(state: ConversationState) -> Optional[SubtopicPlan]:
    if 0 <= state.current_subtopic_index < len(state.subtopics):
        return state.subtopics[state.current_subtopic_index]
    return None


def find_current_subtopic_start_turn_index(
    state: ConversationState,
    current_subtopic: SubtopicPlan,
) -> int:
    marker = f"[SUBTOPIC] {current_subtopic.title}"

    for turn in reversed(state.turns):
        if turn.participant_type == "system" and (
            turn.content or ""
        ).startswith(marker):
            return turn.turn_index

    return 0


def get_turns_from_index(
    state: ConversationState,
    start_turn_index: int,
) -> list[Turn]:
    return [
        turn for turn in state.turns if turn.turn_index >= start_turn_index
    ]


def fallback_subtopic_conclusion(
    *,
    state: ConversationState,
    current_subtopic: SubtopicPlan,
    turns: Sequence[Turn],
    participants: Sequence[DiscussionParticipant],
) -> str:
    speaker_ids: list[str] = []
    for turn in turns:
        if (
            turn.participant_type == "agent"
            and turn.participant_id not in speaker_ids
        ):
            speaker_ids.append(turn.participant_id)

    participant_summaries: list[str] = []
    for participant in participants:
        runtime = state.get_participant_state(participant.participant_id)
        if runtime.summary_text.strip():
            participant_summaries.append(
                f"{participant.participant_id}: {runtime.summary_text.strip()}"
            )

    parts: list[str] = [
        f"Subtopic '{current_subtopic.title}' discussion ended.",
        f"Goal: {current_subtopic.achievement}",
    ]

    if speaker_ids:
        parts.append("Participants involved: " + ", ".join(speaker_ids))

    if participant_summaries:
        parts.append(
            "Latest agent summaries: " + " | ".join(participant_summaries[:3])
        )

    return " ".join(parts).strip()


async def generate_subtopic_conclusion(
    *,
    state: ConversationState,
    current_subtopic: SubtopicPlan,
    participants: Sequence[DiscussionParticipant],
    host_llm: Any | None,
) -> str:
    start_turn_index = find_current_subtopic_start_turn_index(
        state, current_subtopic
    )
    subtopic_turns = get_turns_from_index(state, start_turn_index)

    if host_llm is None:
        return fallback_subtopic_conclusion(
            state=state,
            current_subtopic=current_subtopic,
            turns=subtopic_turns,
            participants=participants,
        )

    messages = build_subtopic_conclusion_messages(
        state=state,
        current_subtopic=current_subtopic,
        subtopic_turns=subtopic_turns,
    )

    try:
        result = await host_llm.ainvoke(messages)
    except Exception:
        return fallback_subtopic_conclusion(
            state=state,
            current_subtopic=current_subtopic,
            turns=subtopic_turns,
            participants=participants,
        )

    payload = extract_llm_payload(result)
    conclusion = str(payload.get("conclusion", "") or "").strip()

    if conclusion:
        return conclusion

    return fallback_subtopic_conclusion(
        state=state,
        current_subtopic=current_subtopic,
        turns=subtopic_turns,
        participants=participants,
    )


async def generate_subtopics(
    *,
    topic: str,
    achievement: str,
    agents: Sequence[AgentSpec],
    host_llm: Any | None,
) -> list[SubtopicPlan]:
    if host_llm is None:
        return _fallback_subtopics(topic=topic, achievement=achievement)

    agent_roles = (
        "\n".join(f"- {agent.display_name} ({agent.role})" for agent in agents)
        or "(none)"
    )

    system = (
        "You are planning a structured technical discussion.\n"
        "Split the session topic into practical subtopics only if decomposition is useful.\n"
        "If one subtopic is enough, return a single item.\n\n"
        "Return JSON only.\n"
        "{"
        '"subtopics":['
        '{"title":"subtopic title","kickoff_message":"kickoff text","achievement":"subtopic achievement"}'
        "]"
        "}"
    )

    user = (
        f"Session topic:\n{topic}\n\n"
        f"Session objective:\n{achievement}\n\n"
        f"Participants:\n{agent_roles}\n\n"
        "Create useful subtopics for the discussion."
    )

    try:
        result = await host_llm.ainvoke(
            [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ]
        )
    except Exception:
        return _fallback_subtopics(topic=topic, achievement=achievement)

    payload = extract_llm_payload(result)
    raw_subtopics = (
        payload.get("subtopics") if isinstance(payload, dict) else None
    )

    subtopics = _coerce_subtopic_plans(
        raw_subtopics,
        topic=topic,
        achievement=achievement,
    )

    if not subtopics:
        return _fallback_subtopics(topic=topic, achievement=achievement)

    return subtopics


async def select_next_speaker(
    agents: Sequence[AgentSpec],
    state: ConversationState,
    *,
    host_llm: Any | None,
) -> AgentSpec | None:
    if not agents:
        return None

    fallback = _fallback_speaker(agents, state)
    if host_llm is None:
        return fallback

    current_subtopic = _get_current_subtopic(state)
    subtopic_title = (
        current_subtopic.title if current_subtopic else state.topic
    )
    subtopic_achievement = (
        current_subtopic.achievement if current_subtopic else state.achievement
    )

    agent_blocks = "\n\n".join(
        _format_agent_runtime(agent, state) for agent in agents
    )

    system = (
        "You are the host moderating a technical discussion.\n"
        "Choose the most suitable next speaker using only visible conversation state.\n"
        "Prefer the agent who can best advance the current subtopic.\n"
        "Keep the discussion balanced when multiple agents are similarly relevant.\n\n"
        f"{RESPONSE_SIZE_RULE}\n"
        "Return JSON only.\n"
        '{"speaker_id":"agent_id or empty"}'
    )

    user = (
        f"Session topic:\n{state.topic}\n\n"
        f"Session objective:\n{state.achievement}\n\n"
        f"Current subtopic:\n{subtopic_title}\n\n"
        f"Current subtopic achievement:\n{subtopic_achievement}\n\n"
        f"Candidate agents:\n{agent_blocks}\n\n"
        f"Recent conversation:\n{_format_recent_turns(state)}\n\n"
        "Choose the next speaker.\n"
        "Return empty speaker_id if nobody should speak now."
    )

    try:
        result = await host_llm.ainvoke(
            [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ]
        )
    except Exception:
        return fallback

    payload = extract_llm_payload(result)
    speaker_id = str(payload.get("speaker_id", "") or "").strip()

    if not speaker_id:
        return None

    for agent in agents:
        if agent.participant_id == speaker_id:
            return agent

    return fallback
