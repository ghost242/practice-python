"""
Turn validation utilities.

This module validates both input state before turn execution and output results
after coordination.

Responsibilities include:
- Verifying topic, subtopic, and participant state consistency.
- Ensuring preconditions for executing a turn are satisfied.
- Validating structural correctness of turn process results.

This validation layer enforces correctness boundaries around the turn workflow.
"""

from __future__ import annotations

from practice_files.practice_ml.discussion.models import (
    Participant,
    SubtopicMemory,
    TopicSessionState,
)
from practice_files.practice_ml.discussion.turn.dto import (
    PrepareTurnInput,
    TurnProcessResult,
    TurnTerminationReason,
)


def validate_prepare_turn_input(data: PrepareTurnInput) -> None:
    """
    Validate input before executing a turn.

    This ensures the turn runner does not operate on invalid session state.
    """

    if not data.session:
        raise ValueError("TopicSessionState is required.")

    if not data.subtopic:
        raise ValueError("SubtopicMemory is required.")

    if not isinstance(data.participants, list):
        raise ValueError("participants must be a list.")

    if not data.subtopic.is_active:
        raise ValueError("Subtopic must be active to run a turn.")

    if data.session.status not in ("OPEN", "RUNNING"):
        raise ValueError(f"Invalid topic status: {data.session.status}")


def validate_participants(participants: list[Participant]) -> None:
    """
    Validate participant collection.
    """

    for p in participants:
        if not p.actor_id:
            raise ValueError("Participant must have actor_id.")

        if not p.display_name:
            raise ValueError(f"Participant {p.actor_id} missing display_name.")


def validate_turn_process_result(result: TurnProcessResult) -> None:
    """
    Validate output after turn execution.

    Ensures consistency between termination reason and payload.
    """

    if result.reason == TurnTerminationReason.COMPLETED:
        if result.completed is None:
            raise ValueError(
                "Completed result must contain completed payload."
            )

        if not result.completed.turn.content:
            raise ValueError("Completed turn must contain content.")

    if result.reason == TurnTerminationReason.SPEAKER_NOT_FOUND:
        if not result.error_message:
            raise ValueError("Missing error message for SPEAKER_NOT_FOUND.")

    if result.reason == TurnTerminationReason.SPEAKER_NOT_AVAILABLE:
        if not result.error_message:
            raise ValueError(
                "Missing error message for SPEAKER_NOT_AVAILABLE."
            )
