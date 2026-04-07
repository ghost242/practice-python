"""
Topic state transition functions.

This module applies runtime state mutation after topic lifecycle events. It is
the mutation boundary of the topic package and is responsible for opening a
topic, updating topic progress during execution, and closing the topic when
the session ends.

Responsibilities include:
- Marking a topic session as open when execution begins.
- Persisting topic progress definition metadata when needed.
- Updating topic session state from completed subtopic execution.
- Finalizing topic status and close metadata on closure.

Centralizing mutation logic prevents hidden side effects in the topic
coordination layer.
"""

from __future__ import annotations

from practice_files.practice_ml.discussion.host.interface import (
    TopicProgressDefinitionResult,
)
from practice_files.practice_ml.discussion.models import (
    TopicSessionState,
    TopicStatus,
)
from practice_files.practice_ml.discussion.subtopic.dto import (
    SubtopicRunResult,
)
from practice_files.practice_ml.discussion.topic.dto import (
    TopicRunResult,
    TopicTerminationReason,
)


def apply_open_topic_transition(
    *,
    session: TopicSessionState,
) -> None:
    """
    Apply state mutation when a topic session begins.

    Args:
        session:
            Current mutable topic session state.
    """
    session.status = TopicStatus.OPEN


def apply_topic_progress_definition(
    *,
    session: TopicSessionState,
    progress_definition: TopicProgressDefinitionResult,
) -> None:
    """
    Apply state updates after topic progress definition is created.

    Args:
        session:
            Current mutable topic session state.
        progress_definition:
            Host-produced topic progress definition.

    Notes:
        The current TopicSessionState model does not persist the planned
        subtopic definitions separately. This transition exists as the
        dedicated mutation hook if that state is added later.
    """
    _ = session
    _ = progress_definition


def apply_subtopic_result_transition(
    *,
    session: TopicSessionState,
    subtopic_result: SubtopicRunResult,
) -> None:
    """
    Apply topic-level state updates after one subtopic session finishes.

    Args:
        session:
            Current mutable topic session state.
        subtopic_result:
            Result of one executed subtopic session.

    Notes:
        Most subtopic-specific counters and state are mutated inside the
        subtopic package. This transition exists for topic-level follow-up
        state changes if needed.
    """
    _ = session
    _ = subtopic_result

    if session.status == TopicStatus.OPEN:
        session.status = TopicStatus.RUNNING


def derive_closed_topic_status(
    result: TopicRunResult,
) -> TopicStatus:
    """
    Derive final topic status from the topic execution result.

    Args:
        result:
            Final result of one topic session execution.

    Returns:
        TopicStatus:
            Final status to persist on the topic session.
    """
    if result.reason in {
        TopicTerminationReason.COMPLETED,
        TopicTerminationReason.HOST_REQUESTED_CLOSE,
        TopicTerminationReason.NO_SUBTOPICS_DEFINED,
        TopicTerminationReason.NO_MORE_SUBTOPICS,
    }:
        return TopicStatus.CLOSED

    if result.reason in {
        TopicTerminationReason.SUBTOPIC_FAILED,
        TopicTerminationReason.VALIDATION_FAILED,
        TopicTerminationReason.FAILED,
    }:
        return TopicStatus.FAILED

    return TopicStatus.CLOSED


def apply_close_topic_transition(
    *,
    session: TopicSessionState,
    result: TopicRunResult,
) -> None:
    """
    Apply state mutation when a topic session ends.

    Args:
        session:
            Current mutable topic session state.
        result:
            Final result of the executed topic session.
    """
    session.status = derive_closed_topic_status(result)

    if result.reason == TopicTerminationReason.HOST_REQUESTED_CLOSE:
        session.close_reason = (
            result.final_next_subtopic_decision.close_reason
            if result.final_next_subtopic_decision is not None
            else ""
        )
    elif result.reason == TopicTerminationReason.NO_SUBTOPICS_DEFINED:
        session.close_reason = "No subtopics were defined for topic progress."
    elif result.reason == TopicTerminationReason.NO_MORE_SUBTOPICS:
        session.close_reason = "No more subtopics available."
    elif result.reason in {
        TopicTerminationReason.SUBTOPIC_FAILED,
        TopicTerminationReason.VALIDATION_FAILED,
        TopicTerminationReason.FAILED,
    }:
        session.close_reason = result.error_message
    else:
        session.close_reason = ""
