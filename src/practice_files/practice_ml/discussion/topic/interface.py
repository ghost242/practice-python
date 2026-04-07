"""
Topic package public interfaces.

This module defines the external contracts used by the application entrypoint
or any higher-level orchestration layer. It provides abstract interfaces for
running one topic session, building topic context, and applying topic state
transitions.

The interfaces expose process-level capabilities without embedding actor-specific
logic, maintaining a clear separation between topic orchestration and actor
behavior owned by the host, participant, and subtopic packages.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from practice_files.practice_ml.discussion.models import (
    Participant,
    TopicSessionState,
)
from practice_files.practice_ml.discussion.subtopic.dto import (
    SubtopicRunResult,
)
from practice_files.practice_ml.discussion.topic.dto import (
    RunTopicInput,
    TopicContext,
    TopicRunResult,
)


@runtime_checkable
class TopicRunnerInterface(Protocol):
    """
    Public interface for executing one topic session.

    This interface is used by the application layer.
    """

    def run_one_topic(
        self,
        data: RunTopicInput,
    ) -> TopicRunResult:
        """
        Execute one topic session.

        Responsibilities:
        - validate input state
        - initialize topic state
        - define progress as subtopics
        - run the subtopic loop
        - close the topic when appropriate
        - return the final topic result
        """
        ...


@runtime_checkable
class TopicContextBuilderInterface(Protocol):
    """
    Interface for building fresh topic context.
    """

    def build_context(
        self,
        session: TopicSessionState,
        participants: list[Participant],
        subtopic_results: list[SubtopicRunResult] | None = None,
    ) -> TopicContext:
        """
        Build a fresh topic-level control context.
        """
        ...


@runtime_checkable
class TopicTransitionInterface(Protocol):
    """
    Interface for applying topic state mutation.
    """

    def apply_transition(
        self,
        session: TopicSessionState,
        result: TopicRunResult,
    ) -> None:
        """
        Apply state changes after topic execution.
        """
        ...


class TopicHostInterface(Protocol):
    def open_topic_session(
        self,
        context: TopicContext,
    ) -> TopicProgressDefinition:
        """Define the initial topic plan and opening control state."""

    def decide_next_subtopic(
        self,
        context: TopicContext,
    ) -> TopicSubtopicDecision:
        """Choose the next subtopic to run, or decide that no further subtopic is needed."""

    def review_topic_progress(
        self,
        context: TopicContext,
    ) -> TopicContinueDecision:
        """Judge whether the topic should continue or close based on current progress."""
