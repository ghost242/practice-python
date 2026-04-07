"""
Topic context construction utilities.

This module builds fresh, read-only context snapshots from the latest topic,
participant, and subtopic runtime state before each topic control cycle. The
context is used by host-driven topic progress definition and next-subtopic
decisions.

Context must be reconstructed during the topic loop to prevent stale control
inputs, because each completed subtopic can change participant progress, topic
state, and the overall discussion trajectory observed by the host.
"""

from __future__ import annotations

from practice_files.practice_ml.discussion.models import (
    Participant,
    TopicSessionState,
)
from practice_files.practice_ml.discussion.subtopic.dto import (
    SubtopicRunResult,
)
from practice_files.practice_ml.discussion.topic.dto import (
    ParticipantProgressView,
    PrepareTopicContextResult,
    SubtopicProgressView,
    TopicContext,
)


def build_participant_progress_view(
    participant: Participant,
) -> ParticipantProgressView:
    """
    Build a read-only participant projection for topic-level control.

    Args:
        participant:
            Mutable runtime participant state.

    Returns:
        ParticipantProgressView:
            Reduced participant state needed for host topic-level decisions.
    """
    return ParticipantProgressView(
        actor_id=participant.actor_id,
        display_name=participant.display_name,
        role=participant.role,
        participation_status=participant.participation_status.value,
        latest_message=participant.latest_message,
        latest_turn_index=participant.latest_turn_index,
        goals=list(participant.goals),
        summary_texts=list(participant.summary_texts),
        goal_evidence_counts=dict(participant.goal_evidence_counts),
    )


def build_subtopic_progress_view_from_result(
    subtopic_result: SubtopicRunResult,
) -> SubtopicProgressView:
    """
    Build a read-only subtopic projection from one subtopic run result.

    Args:
        subtopic_result:
            Final result of one executed subtopic session.

    Returns:
        SubtopicProgressView:
            Reduced subtopic progress information for topic-level control.
    """
    completed = subtopic_result.completed
    subtopic = completed.subtopic if completed is not None else None

    return SubtopicProgressView(
        subtopic_id=subtopic_result.subtopic_id,
        title=subtopic_result.subtopic_title,
        description=subtopic.description if subtopic is not None else "",
        achievement=subtopic.achievement if subtopic is not None else "",
        turn_count=subtopic.turn_count if subtopic is not None else 0,
        summary_text=subtopic.summary_text if subtopic is not None else "",
        status=subtopic.status.value if subtopic is not None else "",
    )


def build_topic_context(
    session: TopicSessionState,
    participants: list[Participant],
    subtopic_results: list[SubtopicRunResult] | None = None,
) -> TopicContext:
    """
    Build a fresh read-only topic context from current runtime state.

    Args:
        session:
            Current mutable topic session state.
        participants:
            Current participant collection.
        subtopic_results:
            Subtopic results observed so far during the topic loop.

    Returns:
        TopicContext:
            Fresh topic-level control context.
    """
    subtopic_results = list(subtopic_results or [])

    participant_views = [
        build_participant_progress_view(participant)
        for participant in participants
    ]

    completed_subtopics = [
        build_subtopic_progress_view_from_result(result)
        for result in subtopic_results
        if result.completed is not None
    ]

    return TopicContext(
        topic_id=session.topic_id,
        topic_title=session.title,
        topic_goal=session.goal,
        topic_turn_count=session.turn_count,
        topic_max_turns=session.max_turns,
        opened_subtopic_count=session.opened_subtopic_count,
        closed_subtopic_count=session.closed_subtopic_count,
        participants=participant_views,
        completed_subtopics=completed_subtopics,
        recent_subtopic_results=subtopic_results,
    )


def prepare_topic_context(
    session: TopicSessionState,
    participants: list[Participant],
    subtopic_results: list[SubtopicRunResult] | None = None,
) -> PrepareTopicContextResult:
    """
    Build and wrap the fresh topic context for one control cycle.

    Args:
        session:
            Current mutable topic session state.
        participants:
            Current participant collection.
        subtopic_results:
            Subtopic results observed so far during the topic loop.

    Returns:
        PrepareTopicContextResult:
            Wrapper around the freshly built topic context.
    """
    context = build_topic_context(
        session=session,
        participants=participants,
        subtopic_results=subtopic_results,
    )
    return PrepareTopicContextResult(context=context)
