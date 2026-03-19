from __future__ import annotations

import asyncio
from typing import Any, Optional, Sequence

from practice_files.practice_ml.conversation_module.decision import (
    generate_subtopic_conclusion,
    generate_subtopics,
    select_next_speaker,
)
from practice_files.practice_ml.conversation_module.exporter import (
    export_discussion,
)
from practice_files.practice_ml.conversation_module.generation import (
    generate_agent_reply,
    generate_final_synthesis,
    update_agent_summary_from_history,
)
from practice_files.practice_ml.conversation_module.types import (
    AgentSpec,
    ConversationState,
    DiscussionParticipant,
    SubtopicPlan,
)


def _ensure_runtime_state_for_all(
    participants: Sequence[DiscussionParticipant],
    state: ConversationState,
) -> None:
    for participant in participants:
        state.ensure_participant_state(participant.participant_id)


def _get_auto_agents(
    participants: Sequence[DiscussionParticipant],
) -> list[AgentSpec]:
    return [
        participant
        for participant in participants
        if isinstance(participant, AgentSpec) and participant.can_self_generate
    ]


def _append_system_turn(
    state: ConversationState,
    content: str,
) -> None:
    state.append_turn(
        participant_id="host",
        participant_type="system",
        content=content,
    )


def _append_agent_turn(
    state: ConversationState,
    agent_id: str,
    content: str,
) -> None:
    state.append_turn(
        participant_id=agent_id,
        participant_type="agent",
        content=content,
    )


def _record_turn_snapshots(
    state: ConversationState,
    participants: Sequence[DiscussionParticipant],
    *,
    speaker_id: str | None,
) -> None:
    last_turn = state.last_turn
    if last_turn is None:
        return

    for participant in participants:
        runtime = state.get_participant_state(participant.participant_id)
        is_speaker = participant.participant_id == speaker_id

        state.append_snapshot(
            turn_index=last_turn.turn_index,
            participant_id=participant.participant_id,
            participant_type=participant.kind,
            content=runtime.latest_reply if is_speaker else "",
            latest_message_index=runtime.last_spoken_turn_index,
            summary=runtime.summary_text or None,
            latest_open_questions=list(runtime.latest_open_questions),
        )


def _default_subtopic_from_session(
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


def _get_current_subtopic(state: ConversationState) -> Optional[SubtopicPlan]:
    if state.current_subtopic_index < 0:
        return None
    if state.current_subtopic_index >= len(state.subtopics):
        return None
    return state.subtopics[state.current_subtopic_index]


def _move_to_next_subtopic(
    state: ConversationState,
    *,
    conclusion: str = "",
) -> bool:
    current = _get_current_subtopic(state)
    if current is not None and current.status != "FINISH":
        if conclusion:
            current.conclusion = conclusion
        current.status = "FINISH"

    next_index = state.current_subtopic_index + 1
    if next_index >= len(state.subtopics):
        return False

    state.current_subtopic_index = next_index
    next_subtopic = state.subtopics[next_index]
    next_subtopic.status = "ONGOING"
    return True


def _mark_reply_runtime(
    state: ConversationState,
    speaker_id: str,
    reply: str,
) -> None:
    runtime = state.get_participant_state(speaker_id)
    runtime.latest_reply = reply
    runtime.times_spoken += 1
    runtime.last_spoken_turn_index = len(state.turns) - 1


def _mark_summary_runtime(
    state: ConversationState,
    participant_id: str,
    summary_text: str,
) -> None:
    runtime = state.get_participant_state(participant_id)
    runtime.summary_text = summary_text


async def _close_current_subtopic(
    *,
    state: ConversationState,
    participants: Sequence[DiscussionParticipant],
    host_llm: Any | None,
) -> bool:
    current_subtopic = _get_current_subtopic(state)
    if current_subtopic is None:
        return False

    conclusion = await generate_subtopic_conclusion(
        state=state,
        current_subtopic=current_subtopic,
        participants=participants,
        host_llm=host_llm,
    )

    if conclusion:
        _append_system_turn(
            state,
            f"[SUBTOPIC CONCLUSION] {current_subtopic.title}\n{conclusion}",
        )
        _record_turn_snapshots(
            state,
            participants,
            speaker_id=None,
        )

    return _move_to_next_subtopic(
        state,
        conclusion=conclusion,
    )


async def _initialize_subtopics(
    *,
    topic: str,
    achievement: str,
    agents: Sequence[AgentSpec],
    host_llm: Any | None,
) -> list[SubtopicPlan]:
    subtopics = await generate_subtopics(
        topic=topic,
        achievement=achievement,
        agents=agents,
        host_llm=host_llm,
    )

    if not subtopics:
        subtopics = _default_subtopic_from_session(topic, achievement)

    if subtopics:
        subtopics[0].status = "ONGOING"

    return subtopics


async def _run_subtopic_turn_loop(
    *,
    state: ConversationState,
    participants: Sequence[DiscussionParticipant],
    max_turns_per_subtopic: int,
    host_llm: Any | None,
) -> bool:
    """
    Returns:
        True  -> moved to next subtopic and should continue
        False -> no more subtopics remain, session should close
    """
    current_subtopic = _get_current_subtopic(state)
    if current_subtopic is None:
        return False

    _append_system_turn(
        state,
        f"[SUBTOPIC] {current_subtopic.title}\n"
        f"[ACHIEVEMENT] {current_subtopic.achievement}\n"
        f"{current_subtopic.kickoff_message}",
    )

    _record_turn_snapshots(
        state,
        participants,
        speaker_id=None,
    )

    auto_agents = _get_auto_agents(participants)

    print(f"\n=== SUBTOPIC START: {current_subtopic.title} ===")
    print("Subtopic achievement:", current_subtopic.achievement)

    for turn_no in range(1, max_turns_per_subtopic + 1):
        print(f"\n--- SUBTOPIC TURN {turn_no} ---")

        speaker = await select_next_speaker(
            agents=auto_agents,
            state=state,
            host_llm=host_llm,
        )

        if speaker is None:
            print("Host found no suitable next speaker for this subtopic.")
            return await _close_current_subtopic(
                state=state,
                participants=participants,
                host_llm=host_llm,
            )

        print("Selected speaker:", speaker.participant_id)

        reply_result = await generate_agent_reply(speaker, state)
        print("Reply:", reply_result.reply)

        _append_agent_turn(state, speaker.participant_id, reply_result.reply)
        _mark_reply_runtime(
            state=state,
            speaker_id=speaker.participant_id,
            reply=reply_result.reply,
        )

        summary_text = await update_agent_summary_from_history(
            agent=speaker,
            state=state,
        )
        print("Updated summary:", summary_text)

        _mark_summary_runtime(
            state=state,
            participant_id=speaker.participant_id,
            summary_text=summary_text,
        )

        _record_turn_snapshots(
            state,
            participants,
            speaker_id=speaker.participant_id,
        )

    print("Reached max turns for current subtopic.")
    return await _close_current_subtopic(
        state=state,
        participants=participants,
        host_llm=host_llm,
    )


async def run_multi_agent_chat(
    *,
    topic: str,
    achievement: str,
    participants: Sequence[DiscussionParticipant],
    max_turns_per_subtopic: int = 8,
    host_llm: Any | None = None,
    export_path: Optional[str] = None,
) -> ConversationState:
    state = ConversationState(
        topic=topic,
        achievement=achievement,
    )
    _ensure_runtime_state_for_all(participants, state)

    agents = _get_auto_agents(participants)
    state.subtopics = await _initialize_subtopics(
        topic=topic,
        achievement=achievement,
        agents=agents,
        host_llm=host_llm,
    )

    print("\n=== DISCUSSION START ===")
    print("Topic:", topic)
    print("Achievement:", achievement)
    print("Subtopics:", [subtopic.title for subtopic in state.subtopics])

    while True:
        current_subtopic = _get_current_subtopic(state)
        if current_subtopic is None:
            break

        should_continue = await _run_subtopic_turn_loop(
            state=state,
            participants=participants,
            max_turns_per_subtopic=max_turns_per_subtopic,
            host_llm=host_llm,
        )

        if not should_continue:
            break

    synthesis_text = await generate_final_synthesis(
        state=state,
        participants=[p for p in participants if isinstance(p, AgentSpec)],
        host_llm=host_llm,
    )
    if synthesis_text:
        _append_system_turn(state, f"[SYNTHESIS] {synthesis_text}")
        _record_turn_snapshots(
            state,
            participants,
            speaker_id=None,
        )

    print("\n=== DISCUSSION END ===")

    if export_path:
        exported_path = export_discussion(state, participants, export_path)
        print("Exported discussion log:", exported_path)

    return state


def run_multi_agent_chat_sync(
    *,
    topic: str,
    achievement: str,
    participants: Sequence[DiscussionParticipant],
    max_turns_per_subtopic: int = 8,
    host_llm: Any | None = None,
    export_path: Optional[str] = None,
) -> ConversationState:
    return asyncio.run(
        run_multi_agent_chat(
            topic=topic,
            achievement=achievement,
            participants=participants,
            max_turns_per_subtopic=max_turns_per_subtopic,
            host_llm=host_llm,
            export_path=export_path,
        )
    )
