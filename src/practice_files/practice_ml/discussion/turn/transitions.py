"""
Turn state transition functions.

This module applies state mutation after a successful turn execution. It is the
single mutation boundary within the turn package.

Responsibilities include:
- Appending the committed turn to subtopic history.
- Updating turn counters at both subtopic and topic levels.
- Refreshing participant runtime state such as latest message and turn index.

Centralizing mutation logic prevents unintended side effects during turn
coordination.
"""

from __future__ import annotations

from practice_files.practice_ml.discussion.models import (
    Participant,
    SubtopicMemory,
    TopicSessionState,
    Turn,
)
from practice_files.practice_ml.discussion.turn.dto import CompletedTurnData


def apply_turn_transition(
    *,
    session: TopicSessionState,
    subtopic: SubtopicMemory,
    participants: list[Participant],
    completed: CompletedTurnData,
) -> None:
    """
    Apply state mutation after a successful turn execution.

    This function is the ONLY place where turn results are committed into
    session state.

    Responsibilities:
    - append turn to subtopic history
    - increment turn counters
    - update participant latest state
    """

    turn: Turn = completed.turn
    speaker = completed.selected_speaker

    # 1. append turn to subtopic history
    subtopic.turns.append(turn)
    subtopic.turn_count += 1

    # 2. update topic-level turn count
    session.turn_count += 1

    # 3. update participant runtime state
    if speaker.participant is not None:
        speaker.participant.latest_message = turn.content
        speaker.participant.latest_turn_index = turn.turn_index


def apply_turn_summary(
    *,
    subtopic: SubtopicMemory,
    summary_text: str,
) -> None:
    """
    Apply summary update after summarization step.

    This is separated from main transition because summarization may be optional
    or executed as a secondary step.
    """

    if not summary_text.strip():
        return

    subtopic.summary_text = summary_text
