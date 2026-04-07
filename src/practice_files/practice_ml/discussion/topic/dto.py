"""
Topic process data models.

This module defines structured data transfer objects used throughout the topic
execution pipeline. A topic represents the outer discussion scope that
progresses through host-defined subtopics until the host decides to close the
topic or a structural stop condition is reached.

The models in this module provide:
- Input contracts for topic execution.
- Read-only context structures for topic-level control decisions.
- Intermediate decision and completion payloads.
- Final result structures for downstream application-level orchestration.

These DTOs keep topic execution explicit, deterministic, and compatible with
the host, participant, and subtopic package boundaries.
"""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field

from practice_files.practice_ml.discussion.host.interface import (
    NextSubtopicDecision,
    SubtopicPlan,
    TopicInput,
    TopicProgressDefinitionResult,
)
from practice_files.practice_ml.discussion.models import (
    Participant,
    TopicSessionState,
)
from practice_files.practice_ml.discussion.subtopic.dto import (
    SubtopicRunResult,
)


class TopicTerminationReason(str, Enum):
    """
    Result category for one topic session execution.

    A topic session is the outer discussion scope. It opens the topic,
    defines progress as subtopics, repeatedly executes subtopic sessions,
    and eventually closes based on host control or structural stop conditions.
    """

    COMPLETED = "COMPLETED"
    HOST_REQUESTED_CLOSE = "HOST_REQUESTED_CLOSE"
    NO_SUBTOPICS_DEFINED = "NO_SUBTOPICS_DEFINED"
    NO_MORE_SUBTOPICS = "NO_MORE_SUBTOPICS"
    SUBTOPIC_FAILED = "SUBTOPIC_FAILED"
    VALIDATION_FAILED = "VALIDATION_FAILED"
    FAILED = "FAILED"


class RunTopicInput(BaseModel):
    """
    Input required to run one topic session.

    The application layer provides the topic input and current participant
    collection. The topic runner uses these inputs to initialize and execute
    one full topic session.
    """

    topic_input: TopicInput
    participants: list[Participant] = Field(default_factory=list)


class InitializeTopicResult(BaseModel):
    """
    Result of opening a topic session.

    This model wraps the mutable topic runtime state returned by host-side
    initialization so the topic runner can continue with a well-defined
    active topic session instance.
    """

    session: TopicSessionState


class PrepareTopicContextResult(BaseModel):
    """
    Fresh topic context snapshot for one control cycle.

    This wrapper exists so the runner can explicitly separate context building
    from topic-level control decisions, similar to the subtopic and turn
    package structure.
    """

    context: "TopicContext"


class ContinueTopicDecision(BaseModel):
    """
    Normalized decision for the next step of the topic loop.

    This model answers the operational question: should the topic runner
    execute another subtopic, or should the topic close now.
    """

    should_continue_topic_loop: bool = True
    should_close_topic: bool = False

    reason: str = ""

    next_subtopic_decision: Optional[NextSubtopicDecision] = None


class CompletedTopicData(BaseModel):
    """
    Successful topic completion payload.

    This contains the final mutable topic session state together with the final
    topic control artifact that explains why the topic ended.
    """

    session: TopicSessionState
    final_next_subtopic_decision: Optional[NextSubtopicDecision] = None
    progress_definition: Optional[TopicProgressDefinitionResult] = None


class TopicRunResult(BaseModel):
    """
    Final result of one topic session execution.

    This model is the public output of the topic runner and is consumed by the
    application layer. It includes both structural outcome metadata and the
    final mutable topic session state when available.
    """

    reason: TopicTerminationReason

    topic_id: str = ""
    topic_title: str = ""

    progress_definition: Optional[TopicProgressDefinitionResult] = None
    subtopic_results: list[SubtopicRunResult] = Field(default_factory=list)

    final_next_subtopic_decision: Optional[NextSubtopicDecision] = None
    completed: Optional[CompletedTopicData] = None

    error_message: str = ""

    @property
    def is_completed(self) -> bool:
        """
        Return whether the topic session finished with a completion payload.
        """
        return (
            self.reason
            in {
                TopicTerminationReason.COMPLETED,
                TopicTerminationReason.HOST_REQUESTED_CLOSE,
                TopicTerminationReason.NO_MORE_SUBTOPICS,
            }
            and self.completed is not None
        )


class TopicContext(BaseModel):
    """
    Read-only topic control context.

    This snapshot is rebuilt during the topic loop so host decisions about
    progress definition, next subtopic selection, and topic closure observe the
    latest topic session state, participant progress, and prior subtopic
    outcomes.
    """

    topic_id: str
    topic_title: str
    topic_goal: str = ""

    topic_turn_count: int = 0
    topic_max_turns: int = 0

    opened_subtopic_count: int = 0
    closed_subtopic_count: int = 0

    participants: list["ParticipantProgressView"] = Field(default_factory=list)
    completed_subtopics: list["SubtopicProgressView"] = Field(
        default_factory=list
    )
    recent_subtopic_results: list[SubtopicRunResult] = Field(
        default_factory=list
    )


class ParticipantProgressView(BaseModel):
    """
    Read-only participant projection for topic-level control decisions.

    The topic layer mainly needs participant progress-oriented fields that help
    the host decide whether another subtopic is likely to produce useful
    progress across the overall discussion goal.
    """

    actor_id: str
    display_name: str
    role: str

    participation_status: str
    latest_message: str = ""
    latest_turn_index: Optional[int] = None

    goals: list[str] = Field(default_factory=list)
    summary_texts: list[str] = Field(default_factory=list)
    goal_evidence_counts: dict[int, int] = Field(default_factory=dict)


class SubtopicProgressView(BaseModel):
    """
    Read-only subtopic projection for topic-level control decisions.

    The topic layer does not need full mutable subtopic state for every
    decision. It mainly needs reduced progress-oriented information about
    previously executed subtopics.
    """

    subtopic_id: str
    title: str
    description: str = ""
    achievement: str = ""

    turn_count: int = 0
    summary_text: str = ""
    status: str = ""
