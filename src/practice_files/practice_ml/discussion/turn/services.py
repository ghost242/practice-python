"""
Turn coordination services.

This module implements pure orchestration logic for a single turn execution.
It coordinates the interaction between the host and speaking actors without
mutating any runtime state.

Responsibilities include:
- Requesting speaker selection from the host.
- Resolving the selected actor against active participants.
- Dispatching message generation to the selected actor.
- Normalizing the output into a commit-ready turn record.

State mutation is intentionally excluded and delegated to the transition layer.
"""

from __future__ import annotations

from typing import Optional

from practice_files.practice_ml.discussion.host.interface import HostInterface
from practice_files.practice_ml.discussion.models import (
    ActorType,
    Host,
    Participant,
    SubtopicMemory,
    TopicSessionState,
    Turn,
)
from practice_files.practice_ml.discussion.participant.interface import (
    GeneratedTurnMessage,
    SpeakingParticipantInterface,
    TurnContext,
)
from practice_files.practice_ml.discussion.turn.dto import (
    CompletedTurnData,
    HostSelectionResult,
    ProducedTurnMessage,
    ResolvedSpeaker,
    TurnProcessResult,
    TurnTerminationReason,
)


def request_host_selection(
    host_runtime: HostInterface,
    host: Host,
    session: TopicSessionState,
    subtopic: SubtopicMemory,
    candidates: list[Participant],
) -> HostSelectionResult:
    """
    Ask the host to select the next speaking actor for the current turn.

    The host is the controller of turn flow. It does not generate the selected
    message itself here. Instead, it chooses which speaking actor should handle
    this turn.
    """
    decision = host_runtime.decide_next_speaker(
        host=host,
        session=session,
        subtopic=subtopic,
        candidates=candidates,
    )

    return HostSelectionResult(
        selected_actor_id=decision.selected_actor_id,
        rationale=decision.rationale,
        host_message=decision.host_message,
    )


def resolve_selected_speaker(
    selected_actor_id: Optional[str],
    participants: list[Participant],
) -> Optional[ResolvedSpeaker]:
    """
    Resolve the host-selected actor id to a runtime participant object.

    In this architecture, selectable speaking actors are represented in the
    participants list. A human user is modeled as a specialized participant, so
    it is resolved through the same lookup path.
    """
    if not selected_actor_id:
        return None

    for participant in participants:
        if participant.actor_id == selected_actor_id:
            return ResolvedSpeaker(
                actor_id=participant.actor_id,
                actor_type=participant.actor_type,
                actor_name=participant.display_name,
                participant=participant,
            )

    return ResolvedSpeaker(
        actor_id=selected_actor_id,
        actor_type=ActorType.PARTICIPANT,
        actor_name="",
        participant=None,
    )


def produce_turn_message(
    participant_runtime: SpeakingParticipantInterface,
    participant: Participant,
    session: TopicSessionState,
    subtopic: SubtopicMemory,
    turn_context: TurnContext,
) -> ProducedTurnMessage:
    """
    Dispatch the selected speaking actor to produce one turn message.

    The participant runtime hides whether the source is an LLM participant or a
    human-backed user participant. The turn service only requires a unified
    speaking interface.
    """
    message: GeneratedTurnMessage = participant_runtime.produce_turn_message(
        participant=participant,
        session=session,
        subtopic=subtopic,
        turn_context=turn_context,
    )

    return ProducedTurnMessage(
        actor_id=participant.actor_id,
        actor_type=participant.actor_type,
        actor_name=participant.display_name,
        content=message.content,
        metadata=dict(message.metadata),
    )


def build_turn_record(
    subtopic: SubtopicMemory,
    produced_message: ProducedTurnMessage,
) -> Turn:
    """
    Convert a produced message into the persisted Turn record.

    The turn record is the committed output of one turn process. It becomes part
    of subtopic history only after the transition layer applies state mutation.
    """
    return Turn(
        turn_index=subtopic.turn_count + 1,
        actor_id=produced_message.actor_id,
        actor_type=produced_message.actor_type,
        actor_name=produced_message.actor_name,
        content=produced_message.content,
        summary_text="",
        subtopic_id=subtopic.subtopic_id,
    )


def execute_turn_process(
    *,
    host_runtime: HostInterface,
    host: Host,
    participant_runtime: SpeakingParticipantInterface,
    session: TopicSessionState,
    subtopic: SubtopicMemory,
    participants: list[Participant],
    turn_context: TurnContext,
) -> TurnProcessResult:
    """
    Execute the pure coordination logic for one turn attempt.

    This function intentionally does not mutate topic or subtopic state.
    It performs only these steps:

    1. Ask the host who should speak.
    2. Resolve that actor against the current participants.
    3. Ask the selected speaking actor to produce one message.
    4. Normalize the output into a commit-ready Turn record.

    State mutation belongs in turn/transitions.py.
    """
    selection = request_host_selection(
        host_runtime=host_runtime,
        host=host,
        session=session,
        subtopic=subtopic,
        candidates=participants,
    )

    if not selection.has_selected_actor:
        if selection.has_host_message:
            return TurnProcessResult(
                reason=TurnTerminationReason.HOST_INTERVENED,
                turn_context=turn_context,
                host_message=selection.host_message,
                rationale=selection.rationale,
            )

        return TurnProcessResult(
            reason=TurnTerminationReason.NO_SPEAKER_SELECTED,
            turn_context=turn_context,
            rationale=selection.rationale,
        )

    resolved = resolve_selected_speaker(
        selected_actor_id=selection.selected_actor_id,
        participants=participants,
    )

    if resolved is None or not resolved.is_found:
        return TurnProcessResult(
            reason=TurnTerminationReason.SPEAKER_NOT_FOUND,
            turn_context=turn_context,
            selected_actor_id=selection.selected_actor_id,
            rationale=selection.rationale,
            error_message=f"Selected actor not found: {selection.selected_actor_id}",
        )

    if not resolved.can_speak:
        return TurnProcessResult(
            reason=TurnTerminationReason.SPEAKER_NOT_AVAILABLE,
            turn_context=turn_context,
            selected_actor_id=resolved.actor_id,
            selected_actor_name=resolved.actor_name,
            rationale=selection.rationale,
            error_message=f"Selected actor cannot speak: {resolved.actor_id}",
        )

    produced_message = produce_turn_message(
        participant_runtime=participant_runtime,
        participant=resolved.participant,
        session=session,
        subtopic=subtopic,
        turn_context=turn_context,
    )

    if not produced_message.content.strip():
        return TurnProcessResult(
            reason=TurnTerminationReason.GENERATION_SKIPPED,
            turn_context=turn_context,
            selected_actor_id=resolved.actor_id,
            selected_actor_name=resolved.actor_name,
            rationale=selection.rationale,
            error_message="Speaking actor returned empty content.",
        )

    turn = build_turn_record(
        subtopic=subtopic,
        produced_message=produced_message,
    )

    completed = CompletedTurnData(
        selected_speaker=resolved,
        produced_message=produced_message,
        turn=turn,
    )

    return TurnProcessResult(
        reason=TurnTerminationReason.COMPLETED,
        turn_context=turn_context,
        selected_actor_id=resolved.actor_id,
        selected_actor_name=resolved.actor_name,
        rationale=selection.rationale,
        completed=completed,
    )
