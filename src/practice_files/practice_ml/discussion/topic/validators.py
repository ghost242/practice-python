"""
Topic validation utilities.

This module validates input state before topic execution and output results
after topic coordination. It enforces structural correctness around the topic
workflow so the runner does not execute against invalid topic input, invalid
participant collections, or inconsistent topic process results.

Responsibilities include:
- Verifying topic input preconditions.
- Validating participant collection integrity.
- Checking consistency of progress definition data.
- Validating structural correctness of topic execution results.
"""

from __future__ import annotations

from practice_files.practice_ml.discussion.models import (
    Participant,
    TopicStatus,
)
from practice_files.practice_ml.discussion.topic.dto import (
    RunTopicInput,
    TopicRunResult,
    TopicTerminationReason,
)


def validate_run_topic_input(data: RunTopicInput) -> None:
    """
    Validate input before executing a topic session.

    Args:
        data:
            Input payload for one topic session run.

    Raises:
        ValueError:
            If required topic input or participant input is invalid.
    """
    if data.topic_input is None:
        raise ValueError("TopicInput is required.")

    if not data.topic_input.topic_id:
        raise ValueError("TopicInput.topic_id is required.")

    if not data.topic_input.title:
        raise ValueError("TopicInput.title is required.")

    if not isinstance(data.participants, list):
        raise ValueError("participants must be a list.")

    if data.topic_input.max_turns < 0:
        raise ValueError(
            "TopicInput.max_turns must be greater than or equal to zero."
        )


def validate_participants(participants: list[Participant]) -> None:
    """
    Validate participant collection used by the topic runner.

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


def validate_initialized_topic_session(session) -> None:
    """
    Validate that an initialized topic session runtime object is usable.

    Args:
        session:
            Mutable topic runtime state returned by initialization.

    Raises:
        ValueError:
            If the initialized topic session is structurally invalid.
    """
    if session is None:
        raise ValueError("Initialized topic session is required.")

    if not session.topic_id:
        raise ValueError("Initialized topic session must have topic_id.")

    if not session.title:
        raise ValueError("Initialized topic session must have title.")

    if session.status not in {
        TopicStatus.PENDING,
        TopicStatus.OPEN,
        TopicStatus.RUNNING,
        TopicStatus.CLOSING,
        TopicStatus.CLOSED,
        TopicStatus.FAILED,
    }:
        raise ValueError(f"Invalid initialized topic status: {session.status}")


def validate_topic_progress_definition(progress_definition) -> None:
    """
    Validate topic progress definition returned by the host.

    Args:
        progress_definition:
            Host-produced topic progress definition.

    Raises:
        ValueError:
            If the progress definition is structurally invalid.
    """
    if progress_definition is None:
        raise ValueError("Topic progress definition is required.")

    seen_subtopic_ids: set[str] = set()

    for subtopic in progress_definition.subtopics:
        if not subtopic.subtopic_id:
            raise ValueError("SubtopicPlan.subtopic_id is required.")

        if not subtopic.title:
            raise ValueError(
                f"SubtopicPlan.title is required: {subtopic.subtopic_id}"
            )

        if subtopic.subtopic_id in seen_subtopic_ids:
            raise ValueError(
                f"Duplicate subtopic_id in topic progress definition: {subtopic.subtopic_id}"
            )

        seen_subtopic_ids.add(subtopic.subtopic_id)


def validate_topic_run_result(result: TopicRunResult) -> None:
    """
    Validate output after topic execution.

    Args:
        result:
            Final result of one topic session execution.

    Raises:
        ValueError:
            If the result is inconsistent with its termination reason.
    """
    if result.reason in {
        TopicTerminationReason.COMPLETED,
        TopicTerminationReason.HOST_REQUESTED_CLOSE,
        TopicTerminationReason.NO_MORE_SUBTOPICS,
    }:
        if result.completed is None:
            raise ValueError(
                "Completed topic result must contain completion payload."
            )

        if result.completed.session is None:
            raise ValueError(
                "Completed topic result must contain final topic session state."
            )

    if result.reason == TopicTerminationReason.SUBTOPIC_FAILED:
        if not result.subtopic_results:
            raise ValueError(
                "SUBTOPIC_FAILED result must include at least one subtopic result."
            )

    if result.reason == TopicTerminationReason.NO_SUBTOPICS_DEFINED:
        if result.progress_definition is None:
            raise ValueError(
                "NO_SUBTOPICS_DEFINED result must include progress_definition."
            )

    if result.reason in {
        TopicTerminationReason.VALIDATION_FAILED,
        TopicTerminationReason.FAILED,
    }:
        if not result.error_message:
            raise ValueError(
                f"{result.reason} result must contain error_message."
            )
