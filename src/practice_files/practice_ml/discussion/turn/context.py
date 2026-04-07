"""
Turn context construction utilities.

This module builds fresh, read-only context snapshots from the latest runtime
state before each turn execution. The context includes topic metadata,
subtopic scope, and recent turn history.

Context must be reconstructed at every turn to avoid stale decision inputs,
as both host selection and speaking behavior depend on the most recent
discussion state.
"""

from __future__ import annotations

from practice_files.practice_ml.discussion.models import (
    Participant,
    SubtopicMemory,
    TopicSessionState,
)
from practice_files.practice_ml.discussion.participant.interface import (
    TurnContext,
)


def build_turn_context(
    session: TopicSessionState,
    subtopic: SubtopicMemory,
    participants: list[Participant],
    recent_turn_limit: int = 12,
) -> TurnContext:
    """
    Build a fresh read-only turn context from current runtime state.

    This function must be called for every turn attempt. Topic and subtopic
    state can change after each committed turn, so reusing an old context
    snapshot would make host selection and speaking behavior stale.

    Args:
        session:
            Current mutable topic session state.
        subtopic:
            Current mutable active subtopic state.
        participants:
            Current participant list. This parameter is included so the context
            builder can be extended later if participant-derived projections are
            added to TurnContext.
        recent_turn_limit:
            Maximum number of recent turns copied into the turn context.

    Returns:
        TurnContext:
            Fresh context snapshot for the next turn.
    """
    _ = participants

    next_turn_index = subtopic.turn_count + 1
    recent_turns = (
        subtopic.turns[-recent_turn_limit:] if recent_turn_limit > 0 else []
    )

    return TurnContext(
        turn_index=next_turn_index,
        topic_id=session.topic_id,
        topic_title=session.title,
        topic_goal=session.goal,
        subtopic_id=subtopic.subtopic_id,
        subtopic_title=subtopic.title,
        subtopic_description=subtopic.description,
        subtopic_achievement=subtopic.achievement,
        recent_turns=list(recent_turns),
    )
