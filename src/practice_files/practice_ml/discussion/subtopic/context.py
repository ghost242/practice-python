"""
Subtopic context construction utilities.

This module builds fresh, read-only context snapshots from the latest topic,
subtopic, participant, and turn runtime state before each subtopic control
cycle. The context is used by host-driven subtopic review and continue-or-close
decisions.

Context must be reconstructed during the subtopic loop to prevent stale control
inputs, because each committed turn can change participant progress, subtopic
state, and the discussion trajectory observed by the host.
"""

from __future__ import annotations

from practice_files.practice_ml.discussion.models import (
    Participant,
    SubtopicMemory,
    TopicSessionState,
)
from practice_files.practice_ml.discussion.subtopic.dto import (
    ParticipantProgressView,
    PrepareSubtopicContextResult,
    SubtopicContext,
)
from practice_files.practice_ml.discussion.turn.dto import TurnProcessResult


def build_participant_progress_view(
    participant: Participant,
) -> ParticipantProgressView:
    """
    Build a read-only participant projection for subtopic-level control.

    Args:
        participant:
            Mutable runtime participant state.

    Returns:
        ParticipantProgressView:
            Reduced participant state needed for host review and subtopic
            continue-or-close decisions.
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


def build_subtopic_context(
    session: TopicSessionState,
    subtopic: SubtopicMemory,
    participants: list[Participant],
    recent_turn_results: list[TurnProcessResult] | None = None,
) -> SubtopicContext:
    """
    Build a fresh read-only subtopic context from current runtime state.

    Args:
        session:
            Current mutable topic session state.
        subtopic:
            Current mutable active subtopic state.
        participants:
            Current participant collection.
        recent_turn_results:
            Recent turn process results observed during the subtopic loop.

    Returns:
        SubtopicContext:
            Fresh subtopic-level control context.
    """
    progress_views = [
        build_participant_progress_view(participant)
        for participant in participants
    ]

    return SubtopicContext(
        topic_id=session.topic_id,
        topic_title=session.title,
        topic_goal=session.goal,
        subtopic_id=subtopic.subtopic_id,
        subtopic_title=subtopic.title,
        subtopic_description=subtopic.description,
        subtopic_achievement=subtopic.achievement,
        subtopic_turn_count=subtopic.turn_count,
        subtopic_summary_text=subtopic.summary_text,
        participants=progress_views,
        recent_turn_results=list(recent_turn_results or []),
    )


def prepare_subtopic_context(
    session: TopicSessionState,
    subtopic: SubtopicMemory,
    participants: list[Participant],
    recent_turn_results: list[TurnProcessResult] | None = None,
) -> PrepareSubtopicContextResult:
    """
    Build and wrap the fresh subtopic context for one control cycle.

    Args:
        session:
            Current mutable topic session state.
        subtopic:
            Current mutable active subtopic state.
        participants:
            Current participant collection.
        recent_turn_results:
            Recent turn process results observed during the subtopic loop.

    Returns:
        PrepareSubtopicContextResult:
            Wrapper around the freshly built subtopic context.
    """
    context = build_subtopic_context(
        session=session,
        subtopic=subtopic,
        participants=participants,
        recent_turn_results=recent_turn_results,
    )
    return PrepareSubtopicContextResult(context=context)
