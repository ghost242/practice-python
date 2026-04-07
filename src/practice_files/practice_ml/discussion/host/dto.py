from __future__ import annotations

"""
Data transfer objects for host-layer orchestration.

This module defines the structured input and output models exchanged between
the orchestration runners/services and a host agent implementation.

The host is responsible for control decisions across three layers:
- topic
- subtopic
- turn

These DTOs should remain provider-agnostic. They describe decision contracts,
not LLM or LangChain integration details.
"""

from pydantic import BaseModel, Field

from practice_files.practice_ml.discussion.models import (
    SubtopicMemory,
    TopicSessionState,
)


# ============================================================================
# Topic-level DTOs
# ============================================================================


class TopicInput(BaseModel):
    """
    Input required to initialize a new topic session.

    Attributes:
        topic_id: Stable identifier for the topic session.
        title: Human-readable topic title.
        goal: Optional session-level goal or achievement target.
        max_turns: Optional topic-level turn budget. A value of zero means
            the concrete host implementation may apply its own default.
    """

    topic_id: str
    title: str
    goal: str = ""
    max_turns: int = 0


class SubtopicPlan(BaseModel):
    """
    Planned subtopic definition produced by the host.

    Attributes:
        subtopic_id: Stable identifier for the planned subtopic.
        title: Human-readable subtopic title.
        description: Optional explanation of the intended scope.
        achievement: Optional achievement target expected before closing
            the subtopic.
    """

    subtopic_id: str
    title: str
    description: str = ""
    achievement: str = ""


class TopicInitializationResult(BaseModel):
    """
    Result of topic-session initialization.

    Attributes:
        session: Initialized mutable topic-session state.
    """

    session: TopicSessionState


class TopicProgressDefinitionResult(BaseModel):
    """
    Result of topic-level planning.

    Attributes:
        subtopics: Ordered list of subtopic plans that define how the topic
            should progress.
    """

    subtopics: list[SubtopicPlan] = Field(default_factory=list)


class NextSubtopicDecision(BaseModel):
    """
    Topic-level decision for selecting the next subtopic or closing the topic.

    Attributes:
        should_close_topic: Whether the topic should close instead of moving
            to another subtopic.
        close_reason: Human-readable explanation for closing the topic.
        next_subtopic: The next subtopic to run when the topic remains open.
    """

    should_close_topic: bool = False
    close_reason: str = ""
    next_subtopic: SubtopicPlan | None = None


# ============================================================================
# Subtopic-level DTOs
# ============================================================================


class SubtopicInitializationResult(BaseModel):
    """
    Result of subtopic-session initialization.

    Attributes:
        subtopic: Initialized mutable subtopic runtime state.
    """

    subtopic: SubtopicMemory


class SubtopicProgressReview(BaseModel):
    """
    Host review of current subtopic progress.

    This object is descriptive rather than imperative. It explains whether the
    subtopic appears to be progressing and what gaps still remain.

    Attributes:
        is_progressing: Whether the host judges the subtopic to still be making
            meaningful progress.
        reason: Human-readable explanation for the progress assessment.
        missing_points: Remaining gaps, unresolved questions, or missing
            evidence that may justify continuing the subtopic.
    """

    is_progressing: bool = True
    reason: str = ""
    missing_points: list[str] = Field(default_factory=list)


class SubtopicControlDecision(BaseModel):
    """
    Subtopic-level control decision.

    This object is imperative rather than descriptive. It tells the orchestration
    layer whether to continue or close the active subtopic.

    Attributes:
        should_continue: Whether another turn should be allowed for the active
            subtopic.
        should_close: Whether the active subtopic should be closed.
        close_reason: Human-readable explanation for closing the subtopic.
    """

    should_continue: bool = True
    should_close: bool = False
    close_reason: str = ""


# ============================================================================
# Turn-level DTOs
# ============================================================================


class SpeakerDecision(BaseModel):
    """
    Turn-level host decision for the next speaking actor.

    In normal operation, the host selects the next actor by id. In exceptional
    cases, the host may provide a host-side message instead.

    Attributes:
        selected_actor_id: Identifier of the next selected actor, if any.
        rationale: Human-readable explanation for the turn-selection decision.
        host_message: Optional host-side message when no participant should be
            selected directly.
    """

    selected_actor_id: str | None = None
    rationale: str = ""
    host_message: str = ""
