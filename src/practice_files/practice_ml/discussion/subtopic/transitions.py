"""
Subtopic state transition functions.

This module applies runtime state mutation after subtopic lifecycle events. It
is the mutation boundary of the subtopic package and is responsible for opening
a subtopic, updating active subtopic state during execution, and closing the
subtopic when the session ends.

Responsibilities include:
- Marking a subtopic as active when execution begins.
- Registering the opened subtopic in topic session state.
- Finalizing subtopic status and active state on closure.
- Updating topic-level opened and closed subtopic counters.
- Persisting subtopic close metadata derived from execution results.

Centralizing mutation logic prevents hidden side effects in the subtopic
coordination layer.
"""

from __future__ import annotations

from practice_files.practice_ml.discussion.models import (
    SubtopicMemory,
    SubtopicStatus,
    TopicSessionState,
)
from practice_files.practice_ml.discussion.subtopic.dto import (
    SubtopicRunResult,
    SubtopicTerminationReason,
)


def apply_open_subtopic_transition(
    *,
    session: TopicSessionState,
    subtopic: SubtopicMemory,
) -> None:
    """
    Apply state mutation when a subtopic session begins.

    Args:
        session:
            Current mutable topic session state.
        subtopic:
            Mutable subtopic runtime state created for the new subtopic session.
    """
    subtopic.is_active = True
    subtopic.status = SubtopicStatus.OPEN

    if not any(
        existing.subtopic_id == subtopic.subtopic_id
        for existing in session.subtopics
    ):
        session.subtopics.append(subtopic)
        session.opened_subtopic_count += 1

    if session.status == session.status.OPEN:
        session.status = session.status.RUNNING


def apply_subtopic_summary(
    *,
    subtopic: SubtopicMemory,
    summary_text: str,
) -> None:
    """
    Apply summary update to the active subtopic.

    Args:
        subtopic:
            Current mutable subtopic runtime state.
        summary_text:
            New summary text to persist on the subtopic.
    """
    if not summary_text.strip():
        return

    subtopic.summary_text = summary_text


def derive_closed_subtopic_status(
    result: SubtopicRunResult,
) -> SubtopicStatus:
    """
    Derive final subtopic status from the subtopic execution result.

    Args:
        result:
            Final result of one subtopic session execution.

    Returns:
        SubtopicStatus:
            Final status to persist on the subtopic.
    """
    if result.reason in {
        SubtopicTerminationReason.COMPLETED,
        SubtopicTerminationReason.HOST_REQUESTED_CLOSE,
        SubtopicTerminationReason.TURN_LIMIT_REACHED,
        SubtopicTerminationReason.NO_PARTICIPANTS_AVAILABLE,
    }:
        return SubtopicStatus.CLOSED

    if result.reason in {
        SubtopicTerminationReason.TURN_FAILED,
        SubtopicTerminationReason.VALIDATION_FAILED,
        SubtopicTerminationReason.FAILED,
    }:
        return SubtopicStatus.FAILED

    return SubtopicStatus.CLOSED


def apply_close_subtopic_transition(
    *,
    session: TopicSessionState,
    subtopic: SubtopicMemory,
    result: SubtopicRunResult,
) -> None:
    """
    Apply state mutation when a subtopic session ends.

    Args:
        session:
            Current mutable topic session state.
        subtopic:
            Mutable subtopic runtime state being closed.
        result:
            Final result of the executed subtopic session.
    """
    subtopic.is_active = False
    subtopic.status = derive_closed_subtopic_status(result)

    if result.completed is not None:
        if result.completed.subtopic.summary_text:
            subtopic.summary_text = result.completed.subtopic.summary_text

    was_already_closed = any(
        existing.subtopic_id == subtopic.subtopic_id and not existing.is_active
        for existing in session.subtopics
    )

    if not was_already_closed:
        session.closed_subtopic_count += 1
