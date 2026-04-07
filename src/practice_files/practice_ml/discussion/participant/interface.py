from __future__ import annotations

from typing import Protocol, runtime_checkable

from pydantic import BaseModel, Field

from practice_files.practice_ml.discussion.models import (
    Participant,
    ParticipantStatus,
    SubtopicMemory,
    TopicSessionState,
    Turn,
    UserParticipant,
)


# ============================================================================
# Turn-level DTOs
# ============================================================================


class TurnContext(BaseModel):
    """
    Read-only input context for producing one turn message.

    This context is built by the turn layer and passed to a speaking actor
    selected by the host.
    """

    turn_index: int
    topic_id: str
    topic_title: str
    topic_goal: str = ""

    subtopic_id: str
    subtopic_title: str
    subtopic_description: str = ""
    subtopic_achievement: str = ""

    recent_turns: list[Turn] = Field(default_factory=list)


class GeneratedTurnMessage(BaseModel):
    """
    Result of one speaking action by a participant or user.

    This is the raw message output before turn registration finalizes it into
    subtopic history.
    """

    actor_id: str
    content: str
    metadata: dict[str, str] = Field(default_factory=dict)


# ============================================================================
# Summary / evaluation DTOs
# ============================================================================


class ContributionSummary(BaseModel):
    """
    Summary of one participant's recent contribution interval.

    This is used to build compact memory for later host decisions and for
    participant-level progress evaluation.
    """

    actor_id: str
    summary_text: str


class GoalProgressEvaluation(BaseModel):
    """
    Evaluation of the participant's current goal progress inside the discussion.
    """

    actor_id: str
    participation_status: ParticipantStatus
    reason: str = ""
    goal_evidence_counts: dict[int, int] = Field(default_factory=dict)


# ============================================================================
# Participant interfaces
# ============================================================================


@runtime_checkable
class SpeakingParticipantInterface(Protocol):
    """
    Common speaking interface for participant-like actors.

    Both LLM participants and human users should fit this runtime shape so the
    turn runner can dispatch uniformly after the host selects the next speaker.
    """

    def produce_turn_message(
        self,
        participant: Participant | UserParticipant,
        session: TopicSessionState,
        subtopic: SubtopicMemory,
        turn_context: TurnContext,
    ) -> GeneratedTurnMessage:
        """
        Produce one message for the current turn.

        For LLM participants, this usually means generation.
        For user participants, this usually means accepting external human input.
        """
        ...


@runtime_checkable
class ParticipantSummaryInterface(Protocol):
    """
    Summary interface for participant contribution tracking.
    """

    def summarize_contribution(
        self,
        participant: Participant,
        session: TopicSessionState,
        subtopic: SubtopicMemory,
    ) -> ContributionSummary:
        """
        Produce a compact summary of the participant's recent contribution.
        """
        ...


@runtime_checkable
class ParticipantEvaluationInterface(Protocol):
    """
    Evaluation interface for participant progress toward discussion goals.
    """

    def evaluate_goal_progress(
        self,
        participant: Participant,
        session: TopicSessionState,
        subtopic: SubtopicMemory,
    ) -> GoalProgressEvaluation:
        """
        Evaluate whether the participant should remain ongoing, wait, or finish.
        """
        ...


@runtime_checkable
class ParticipantInterface(
    SpeakingParticipantInterface,
    ParticipantSummaryInterface,
    ParticipantEvaluationInterface,
    Protocol,
):
    """
    Aggregate interface for a full LLM participant runtime.
    """

    pass


@runtime_checkable
class UserParticipantInterface(SpeakingParticipantInterface, Protocol):
    """
    Runtime interface for a human user participant.

    The user shares the same turn production surface as a participant, but
    usually does not require synthetic summary/evaluation behavior unless the
    application chooses to treat the user identically to LLM participants.
    """

    pass
