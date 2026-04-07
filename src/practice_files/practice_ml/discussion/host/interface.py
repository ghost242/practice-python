from __future__ import annotations

from typing import Protocol, Sequence, runtime_checkable

from pydantic import BaseModel, Field

from practice_files.practice_ml.discussion.models import (
    Host,
    Participant,
    TopicSessionState,
    SubtopicMemory,
)


# ============================================================================
# Topic-level DTOs
# ============================================================================


class TopicInput(BaseModel):
    """
    Input required to initialize a new topic session.
    """

    topic_id: str
    title: str
    goal: str = ""
    max_turns: int = 0


class SubtopicPlan(BaseModel):
    """
    Host-defined plan unit for progressing the topic through subtopics.
    """

    subtopic_id: str
    title: str
    description: str = ""
    achievement: str = ""


class TopicInitializationResult(BaseModel):
    """
    Result returned after the host initializes the topic session.
    """

    session: TopicSessionState


class TopicProgressDefinitionResult(BaseModel):
    """
    Result returned after the host defines progress units for the topic.
    """

    subtopics: list[SubtopicPlan] = Field(default_factory=list)


class NextSubtopicDecision(BaseModel):
    """
    Decision about what subtopic should run next.

    If `should_close_topic` is true, `next_subtopic` may be omitted.
    """

    should_close_topic: bool = False
    close_reason: str = ""
    next_subtopic: SubtopicPlan | None = None


# ============================================================================
# Subtopic-level DTOs
# ============================================================================


class SubtopicInitializationResult(BaseModel):
    """
    Result returned after the host initializes a subtopic session.
    """

    subtopic: SubtopicMemory


class SubtopicProgressReview(BaseModel):
    """
    Host review of current subtopic progress.
    """

    is_progressing: bool = True
    reason: str = ""
    missing_points: list[str] = Field(default_factory=list)


class SubtopicControlDecision(BaseModel):
    """
    Host control decision for the current subtopic loop.
    """

    should_continue: bool = True
    should_close: bool = False
    close_reason: str = ""


# ============================================================================
# Turn-level DTOs
# ============================================================================


class SpeakerDecision(BaseModel):
    """
    Host decision for selecting the next speaking actor in a turn.

    Exactly one of `selected_actor_id` or `host_message` is usually expected.
    """

    selected_actor_id: str | None = None
    rationale: str = ""
    host_message: str = ""


# ============================================================================
# Host interfaces
# ============================================================================


@runtime_checkable
class TopicHostInterface(Protocol):
    """
    Topic-layer control interface for the host.

    The host uses this interface to open the topic session, define topic
    progress through subtopics, and choose the next subtopic to run.
    """

    def initialize_topic(
        self,
        host: Host,
        topic_input: TopicInput,
    ) -> TopicInitializationResult:
        """
        Initialize the outer topic session.
        """
        ...

    def define_topic_progress(
        self,
        host: Host,
        session: TopicSessionState,
    ) -> TopicProgressDefinitionResult:
        """
        Define topic progress as a sequence of subtopic plans.
        """
        ...

    def decide_next_subtopic(
        self,
        host: Host,
        session: TopicSessionState,
    ) -> NextSubtopicDecision:
        """
        Decide which subtopic should run next, or whether the topic should close.
        """
        ...


@runtime_checkable
class SubtopicHostInterface(Protocol):
    """
    Subtopic-layer control interface for the host.

    The host uses this interface to initialize each subtopic, review progress,
    and decide whether to continue with another turn or close the subtopic.
    """

    def initialize_subtopic(
        self,
        host: Host,
        session: TopicSessionState,
        subtopic_plan: SubtopicPlan,
    ) -> SubtopicInitializationResult:
        """
        Initialize one subtopic session from a planned subtopic definition.
        """
        ...

    def review_subtopic_progress(
        self,
        host: Host,
        session: TopicSessionState,
        subtopic: SubtopicMemory,
        participants: Sequence[Participant],
    ) -> SubtopicProgressReview:
        """
        Review current progress inside the active subtopic.
        """
        ...

    def decide_continue_or_close_subtopic(
        self,
        host: Host,
        session: TopicSessionState,
        subtopic: SubtopicMemory,
        participants: Sequence[Participant],
    ) -> SubtopicControlDecision:
        """
        Decide whether the current subtopic should continue or close.
        """
        ...


@runtime_checkable
class TurnHostInterface(Protocol):
    """
    Turn-layer control interface for the host.

    The host uses this interface to decide who should speak on the next turn.
    """

    def decide_next_speaker(
        self,
        host: Host,
        session: TopicSessionState,
        subtopic: SubtopicMemory,
        candidates: Sequence[Participant],
    ) -> SpeakerDecision:
        """
        Select the next speaking actor for the current turn.
        """
        ...


@runtime_checkable
class HostInterface(
    TopicHostInterface,
    SubtopicHostInterface,
    TurnHostInterface,
    Protocol,
):
    """
    Aggregate interface for a fully capable host controller.
    """

    pass
