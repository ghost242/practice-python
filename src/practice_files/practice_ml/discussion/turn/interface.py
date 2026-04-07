"""
Turn package public interfaces.

This module defines the external contracts used by higher-level orchestration
layers, such as the subtopic runner.

It provides abstract interfaces for:
- Executing a single turn.
- Building turn context.
- Applying state transitions.

The interfaces expose process-level capabilities without embedding actor-specific
logic, maintaining a clear separation between orchestration and actor behavior.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from practice_files.practice_ml.discussion.models import (
    Participant,
    SubtopicMemory,
    TopicSessionState,
)
from practice_files.practice_ml.discussion.turn.dto import (
    PrepareTurnInput,
    TurnProcessResult,
)


@runtime_checkable
class TurnRunnerInterface(Protocol):
    """
    Public interface for executing one turn.

    This interface is used by the subtopic layer.
    """

    def run_one_turn(
        self,
        data: PrepareTurnInput,
    ) -> TurnProcessResult:
        """
        Execute one turn process.

        Responsibilities:
        - build fresh context
        - validate input
        - coordinate host + participant interaction
        - return result (without mutating state)
        """
        ...


@runtime_checkable
class TurnContextBuilderInterface(Protocol):
    """
    Interface for building fresh turn context.
    """

    def build_context(
        self,
        session: TopicSessionState,
        subtopic: SubtopicMemory,
        participants: list[Participant],
    ): ...


@runtime_checkable
class TurnTransitionInterface(Protocol):
    """
    Interface for applying turn state mutation.
    """

    def apply_transition(
        self,
        session: TopicSessionState,
        subtopic: SubtopicMemory,
        participants: list[Participant],
        result: TurnProcessResult,
    ) -> None:
        """
        Apply state changes after a completed turn.
        """
        ...
