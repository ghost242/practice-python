"""
Subtopic process data models.

This module defines structured data transfer objects used throughout the
subtopic execution pipeline. A subtopic represents a focused discussion scope
that repeatedly runs turn execution under host control until the host decides
to continue or close the subtopic.

The models in this module provide:
- Input contracts for subtopic execution.
- Read-only context structures for subtopic-level control decisions.
- Intermediate decision and completion payloads.
- Final result structures for downstream topic-level orchestration.

These DTOs keep subtopic execution explicit, deterministic, and compatible with
the host, participant, and turn package boundaries.
"""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field

from practice_files.practice_ml.discussion.host.interface import (
    SubtopicControlDecision,
    SubtopicPlan,
    SubtopicProgressReview,
)
from practice_files.practice_ml.discussion.models import (
    Participant,
    SubtopicMemory,
    TopicSessionState,
)
from practice_files.practice_ml.discussion.turn.dto import TurnProcessResult


class SubtopicTerminationReason(str, Enum):
    """
    Result category for one subtopic session execution.

    A subtopic session is a focused discussion scope that repeatedly runs turn
    execution until the host decides the subtopic should close, or until the
    process reaches a structural stop condition.
    """

    COMPLETED = "COMPLETED"
    HOST_REQUESTED_CLOSE = "HOST_REQUESTED_CLOSE"
    NO_PARTICIPANTS_AVAILABLE = "NO_PARTICIPANTS_AVAILABLE"
    TURN_LIMIT_REACHED = "TURN_LIMIT_REACHED"
    TURN_FAILED = "TURN_FAILED"
    VALIDATION_FAILED = "VALIDATION_FAILED"
    FAILED = "FAILED"


class RunSubtopicInput(BaseModel):
    """
    Input required to run one subtopic session.

    The topic layer provides the current topic session state, the host-selected
    subtopic plan, and the current participant collection. The subtopic runner
    uses these inputs to initialize and execute one focused discussion session.
    """

    session: TopicSessionState
    subtopic_plan: SubtopicPlan
    participants: list[Participant] = Field(default_factory=list)

    max_turns: int = 0


class InitializeSubtopicResult(BaseModel):
    """
    Result of opening a subtopic session.

    This model wraps the mutable subtopic runtime state returned by host-side
    initialization so the subtopic runner can continue with a well-defined
    active subtopic instance.
    """

    subtopic: SubtopicMemory


class PrepareSubtopicContextResult(BaseModel):
    """
    Fresh subtopic context snapshot for one control cycle.

    This wrapper exists so the runner can explicitly separate context building
    from control decisions, similar to the turn package structure.
    """

    context: "SubtopicContext"


class ContinueSubtopicDecision(BaseModel):
    """
    Normalized decision for the next step of the subtopic loop.

    This model combines review and control intent into one runner-facing shape.
    It answers the operational question: should another turn run, or should the
    current subtopic close now.
    """

    should_continue_turn_loop: bool = True
    should_close_subtopic: bool = False

    reason: str = ""

    progress_review: Optional[SubtopicProgressReview] = None
    control_decision: Optional[SubtopicControlDecision] = None


class CompletedSubtopicData(BaseModel):
    """
    Successful subtopic completion payload.

    This contains the final mutable subtopic state together with the final
    review/control artifacts that explain why the subtopic ended.
    """

    subtopic: SubtopicMemory
    final_progress_review: Optional[SubtopicProgressReview] = None
    final_control_decision: Optional[SubtopicControlDecision] = None


class SubtopicRunResult(BaseModel):
    """
    Final result of one subtopic session execution.

    This model is the public output of the subtopic runner and is consumed by
    the topic layer. It includes both structural outcome metadata and the final
    mutable subtopic state when available.
    """

    reason: SubtopicTerminationReason

    subtopic_id: str = ""
    subtopic_title: str = ""

    turn_results: list[TurnProcessResult] = Field(default_factory=list)

    final_progress_review: Optional[SubtopicProgressReview] = None
    final_control_decision: Optional[SubtopicControlDecision] = None

    completed: Optional[CompletedSubtopicData] = None

    error_message: str = ""

    @property
    def is_completed(self) -> bool:
        """
        Return whether the subtopic session finished with a completion payload.
        """
        return (
            self.reason
            in {
                SubtopicTerminationReason.COMPLETED,
                SubtopicTerminationReason.HOST_REQUESTED_CLOSE,
                SubtopicTerminationReason.TURN_LIMIT_REACHED,
            }
            and self.completed is not None
        )


class SubtopicContext(BaseModel):
    """
    Read-only subtopic control context.

    This snapshot is rebuilt during the subtopic loop so host review and
    continue/close decisions observe the latest session, subtopic, participant,
    and turn state.

    The subtopic layer depends on participant progress because the host may
    choose to continue or close a subtopic based on whether participants still
    have meaningful contribution potential.
    """

    topic_id: str
    topic_title: str
    topic_goal: str = ""

    subtopic_id: str
    subtopic_title: str
    subtopic_description: str = ""
    subtopic_achievement: str = ""

    subtopic_turn_count: int = 0
    subtopic_summary_text: str = ""

    participants: list["ParticipantProgressView"] = Field(default_factory=list)

    recent_turn_results: list[TurnProcessResult] = Field(default_factory=list)


class ParticipantProgressView(BaseModel):
    """
    Read-only participant projection for subtopic-level control decisions.

    The subtopic layer does not need the participant's full mutable state for
    every decision. It mainly needs progress-oriented fields that help the host
    determine whether further turns are likely to produce useful discussion.
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
