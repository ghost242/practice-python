"""
Subtopic validation utilities.

This module validates input state before subtopic execution and output results
after subtopic coordination. It enforces structural correctness around the
subtopic workflow so the runner does not execute against invalid topic state,
invalid participant collections, or inconsistent subtopic process results.

Responsibilities include:
- Verifying topic session and subtopic plan preconditions.
- Validating participant collection integrity.
- Checking consistency of subtopic execution results.
- Guarding active subtopic assumptions during control flow.
"""

from __future__ import annotations

from practice_files.practice_ml.discussion.models import (
    Participant,
    TopicStatus,
)
from practice_files.practice_ml.discussion.subtopic.dto import (
    RunSubtopicInput,
    SubtopicRunResult,
    SubtopicTerminationReason,
)


def validate_run_subtopic_input(data: RunSubtopicInput) -> None:
    """
    Validate input before executing a subtopic session.

    Args:
        data:
            Input payload for one subtopic session run.

    Raises:
        ValueError:
            If required topic, subtopic, or participant input is invalid.
    """
    if data.session is None:
        raise ValueError("TopicSessionState is required.")

    if data.subtopic_plan is None:
        raise ValueError("SubtopicPlan is required.")

    if not data.subtopic_plan.subtopic_id:
        raise ValueError("SubtopicPlan.subtopic_id is required.")

    if not data.subtopic_plan.title:
        raise ValueError("SubtopicPlan.title is required.")

    if not isinstance(data.participants, list):
        raise ValueError("participants must be a list.")

    if data.session.status not in {TopicStatus.OPEN, TopicStatus.RUNNING}:
        raise ValueError(
            f"Invalid topic status for subtopic execution: {data.session.status}"
        )

    if data.max_turns < 0:
        raise ValueError("max_turns must be greater than or equal to zero.")


def validate_participants(participants: list[Participant]) -> None:
    """
    Validate participant collection used by the subtopic runner.

    Args:
        participants:
            Runtime participant collection.

    Raises:
        ValueError:
            If a participant is missing required identity fields.
    """
    for participant in participants:
        if not participant.actor_id:
            raise ValueError("Participant.actor_id is required.")

        if not participant.display_name:
            raise ValueError(
                f"Participant display_name is required: {participant.actor_id}"
            )

        if not participant.role:
            raise ValueError(
                f"Participant role is required: {participant.actor_id}"
            )


def validate_initialized_subtopic(subtopic) -> None:
    """
    Validate that an initialized subtopic runtime object is usable.

    Args:
        subtopic:
            Mutable subtopic runtime state returned by initialization.

    Raises:
        ValueError:
            If the initialized subtopic is structurally invalid.
    """
    if subtopic is None:
        raise ValueError("Initialized subtopic is required.")

    if not subtopic.subtopic_id:
        raise ValueError("Initialized subtopic must have subtopic_id.")

    if not subtopic.title:
        raise ValueError("Initialized subtopic must have title.")


def validate_subtopic_run_result(result: SubtopicRunResult) -> None:
    """
    Validate output after subtopic execution.

    Args:
        result:
            Final result of one subtopic session execution.

    Raises:
        ValueError:
            If the result is inconsistent with its termination reason.
    """
    if result.reason in {
        SubtopicTerminationReason.COMPLETED,
        SubtopicTerminationReason.HOST_REQUESTED_CLOSE,
        SubtopicTerminationReason.TURN_LIMIT_REACHED,
    }:
        if result.completed is None:
            raise ValueError(
                "Completed subtopic result must contain completion payload."
            )

        if result.completed.subtopic is None:
            raise ValueError(
                "Completed subtopic result must contain final subtopic state."
            )

    if result.reason == SubtopicTerminationReason.TURN_FAILED:
        if not result.turn_results:
            raise ValueError(
                "TURN_FAILED result must include at least one turn result."
            )

    if result.reason in {
        SubtopicTerminationReason.VALIDATION_FAILED,
        SubtopicTerminationReason.FAILED,
    }:
        if not result.error_message:
            raise ValueError(
                f"{result.reason} result must contain error_message."
            )
