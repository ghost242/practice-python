"""
Subtopic package public interfaces.

This module defines the external contracts used by higher-level orchestration
layers, such as the topic runner. It provides abstract interfaces for running
one subtopic session, building subtopic context, and applying subtopic state
transitions.

The interfaces expose process-level capabilities without embedding actor-specific
logic, maintaining a clear separation between subtopic orchestration and actor
behavior owned by the host and participant packages.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from practice_files.practice_ml.discussion.models import (
    Participant,
    SubtopicMemory,
    TopicSessionState,
)
from practice_files.practice_ml.discussion.subtopic.dto import (
    RunSubtopicInput,
    SubtopicContext,
    SubtopicRunResult,
)
from practice_files.practice_ml.discussion.turn.dto import TurnProcessResult


@runtime_checkable
class SubtopicRunnerInterface(Protocol):
    """
    Public interface for executing one subtopic session.

    This interface is used by the topic layer.
    """

    def run_one_subtopic(
        self,
        data: RunSubtopicInput,
    ) -> SubtopicRunResult:
        """
        Execute one subtopic session.

        Responsibilities:
        - validate input state
        - initialize subtopic state
        - run the turn loop
        - review progress and close when appropriate
        - return the final subtopic result
        """
        ...


@runtime_checkable
class SubtopicContextBuilderInterface(Protocol):
    """
    Interface for building fresh subtopic context.
    """

    def build_context(
        self,
        session: TopicSessionState,
        subtopic: SubtopicMemory,
        participants: list[Participant],
        recent_turn_results: list[TurnProcessResult] | None = None,
    ) -> SubtopicContext:
        """
        Build a fresh subtopic-level control context.
        """
        ...


@runtime_checkable
class SubtopicTransitionInterface(Protocol):
    """
    Interface for applying subtopic state mutation.
    """

    def apply_transition(
        self,
        session: TopicSessionState,
        subtopic: SubtopicMemory,
        result: SubtopicRunResult,
    ) -> None:
        """
        Apply state changes after subtopic execution.
        """
        ...
