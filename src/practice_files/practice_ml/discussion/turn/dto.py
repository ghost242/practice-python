"""
Turn process data models.

This module defines structured data transfer objects used throughout the turn
execution pipeline. A turn represents a single execution attempt in which the
host selects a speaking actor and the selected actor produces one message.

The models in this module provide:
- Input contracts for turn execution.
- Intermediate representations for speaker resolution and message production.
- Final result structures for downstream validation and state transition.

These DTOs ensure deterministic and inspectable behavior across the turn
orchestration flow.
"""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field

from practice_files.practice_ml.discussion.models import (
    ActorType,
    Participant,
    SubtopicMemory,
    TopicSessionState,
    Turn,
)
from practice_files.practice_ml.discussion.participant.interface import (
    TurnContext,
)


class TurnTerminationReason(str, Enum):
    """
    Result category for one turn execution attempt.

    A turn in this system is the execution unit where the host selects one
    actor and the selected actor produces one message. This enum classifies
    the outcome of that process.
    """

    COMPLETED = "COMPLETED"
    NO_SPEAKER_SELECTED = "NO_SPEAKER_SELECTED"
    HOST_INTERVENED = "HOST_INTERVENED"
    SPEAKER_NOT_FOUND = "SPEAKER_NOT_FOUND"
    SPEAKER_NOT_AVAILABLE = "SPEAKER_NOT_AVAILABLE"
    GENERATION_SKIPPED = "GENERATION_SKIPPED"
    FAILED = "FAILED"


class PrepareTurnInput(BaseModel):
    """
    Input to execute one turn inside an already opened subtopic session.

    The turn package does not own topic or subtopic lifecycle. It only consumes
    the current runtime state needed to coordinate one turn.
    """

    session: TopicSessionState
    subtopic: SubtopicMemory
    participants: list[Participant] = Field(default_factory=list)


class PrepareTurnContextResult(BaseModel):
    """
    Fresh turn context generated from the latest runtime state.

    This is separated so the runner can explicitly build and validate context
    before the turn process starts.
    """

    turn_context: TurnContext


class ResolvedSpeaker(BaseModel):
    """
    Runtime result of resolving a host-selected actor id.

    The host returns an actor id. The turn service resolves that id against the
    current participant list and exposes both identity metadata and the actual
    participant object if found.
    """

    actor_id: str
    actor_type: ActorType
    actor_name: str
    participant: Optional[Participant] = None

    @property
    def is_found(self) -> bool:
        """
        Return whether the selected actor id was matched to a runtime participant.
        """
        return self.participant is not None

    @property
    def can_speak(self) -> bool:
        """
        Return whether the resolved participant is currently allowed to speak.
        """
        return self.participant is not None and self.participant.can_speak


class HostSelectionResult(BaseModel):
    """
    Normalized host selection result for one turn.

    The host may select a speaking actor, or it may choose not to select any
    actor and instead provide a host-side intervention message.
    """

    selected_actor_id: Optional[str] = None
    rationale: str = ""
    host_message: str = ""

    @property
    def has_selected_actor(self) -> bool:
        """
        Return whether the host selected an actor for this turn.
        """
        return bool(self.selected_actor_id)

    @property
    def has_host_message(self) -> bool:
        """
        Return whether the host produced a control/intervention message.
        """
        return bool(self.host_message)


class ProducedTurnMessage(BaseModel):
    """
    Normalized speaking result from a participant or user.

    This is the output returned by the speaking runtime before it is converted
    into a persisted Turn record.
    """

    actor_id: str
    actor_type: ActorType
    actor_name: str
    content: str
    metadata: dict[str, str] = Field(default_factory=dict)


class CompletedTurnData(BaseModel):
    """
    Successful turn payload before state transition is applied.

    The runner can pass this object to the transition layer to commit the
    actual state mutation.
    """

    selected_speaker: ResolvedSpeaker
    produced_message: ProducedTurnMessage
    turn: Turn


class TurnProcessResult(BaseModel):
    """
    Final result for one turn execution attempt.

    This model captures both successful and non-successful outcomes so the
    subtopic runner can decide whether to continue or close the current loop.
    """

    reason: TurnTerminationReason
    turn_context: Optional[TurnContext] = None

    selected_actor_id: Optional[str] = None
    selected_actor_name: str = ""

    host_message: str = ""
    rationale: str = ""
    error_message: str = ""

    completed: Optional[CompletedTurnData] = None

    @property
    def is_completed(self) -> bool:
        """
        Return whether the turn completed successfully and contains commit-ready data.
        """
        return (
            self.reason == TurnTerminationReason.COMPLETED
            and self.completed is not None
        )
