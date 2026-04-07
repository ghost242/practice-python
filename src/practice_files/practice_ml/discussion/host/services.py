from __future__ import annotations

"""
Service layer for host orchestration responsibilities.

This module provides thin application services that call the injected
host controller through `HostInterface`. The service layer is responsible
for:
- validating basic call preconditions,
- keeping orchestration code outside runners concise,
- preserving a clear boundary between control policy and workflow plumbing.

The service layer should not implement host decision policy itself.
Decision policy belongs to the concrete implementation of `HostInterface`.
"""

from dataclasses import dataclass
from typing import Sequence

from practice_files.practice_ml.discussion.models import (
    Host,
    Participant,
    SubtopicMemory,
    TopicSessionState,
)
from practice_files.practice_ml.discussion.host.interface import (
    HostInterface,
    NextSubtopicDecision,
    SpeakerDecision,
    SubtopicControlDecision,
    SubtopicInitializationResult,
    SubtopicPlan,
    SubtopicProgressReview,
    TopicInitializationResult,
    TopicInput,
    TopicProgressDefinitionResult,
)


@dataclass(slots=True)
class HostServices:
    """
    Application service facade for host control operations.

    This service delegates all decision-making to the provided
    `HostInterface` implementation. It exists to centralize orchestration
    entry points so runners do not depend directly on raw host policy
    objects.
    """

    host_controller: HostInterface

    def initialize_topic(
        self,
        host: Host,
        topic_input: TopicInput,
    ) -> TopicInitializationResult:
        """
        Initialize a new topic session through the host controller.

        Args:
            host: Host actor responsible for orchestration.
            topic_input: Topic-level input for session initialization.

        Returns:
            TopicInitializationResult containing the initialized
            topic session state.

        Raises:
            ValueError: If topic identity or title is missing.
        """
        if not topic_input.topic_id.strip():
            raise ValueError("topic_input.topic_id must not be empty.")
        if not topic_input.title.strip():
            raise ValueError("topic_input.title must not be empty.")

        return self.host_controller.initialize_topic(
            host=host,
            topic_input=topic_input,
        )

    def define_topic_progress(
        self,
        host: Host,
        session: TopicSessionState,
    ) -> TopicProgressDefinitionResult:
        """
        Define the topic progression plan as subtopics.

        Args:
            host: Host actor responsible for orchestration.
            session: Current topic session state.

        Returns:
            TopicProgressDefinitionResult with the proposed subtopic plan.
        """
        return self.host_controller.define_topic_progress(
            host=host,
            session=session,
        )

    def decide_next_subtopic(
        self,
        host: Host,
        session: TopicSessionState,
    ) -> NextSubtopicDecision:
        """
        Decide the next subtopic to run, or whether to close the topic.

        Args:
            host: Host actor responsible for orchestration.
            session: Current topic session state.

        Returns:
            NextSubtopicDecision describing the next topic-level action.
        """
        return self.host_controller.decide_next_subtopic(
            host=host,
            session=session,
        )

    def initialize_subtopic(
        self,
        host: Host,
        session: TopicSessionState,
        subtopic_plan: SubtopicPlan,
    ) -> SubtopicInitializationResult:
        """
        Initialize a subtopic session from a subtopic plan.

        Args:
            host: Host actor responsible for orchestration.
            session: Parent topic session state.
            subtopic_plan: Plan describing the subtopic to initialize.

        Returns:
            SubtopicInitializationResult containing initialized
            subtopic memory/state.

        Raises:
            ValueError: If subtopic identity or title is missing.
        """
        if not subtopic_plan.subtopic_id.strip():
            raise ValueError("subtopic_plan.subtopic_id must not be empty.")
        if not subtopic_plan.title.strip():
            raise ValueError("subtopic_plan.title must not be empty.")

        return self.host_controller.initialize_subtopic(
            host=host,
            session=session,
            subtopic_plan=subtopic_plan,
        )

    def review_subtopic_progress(
        self,
        host: Host,
        session: TopicSessionState,
        subtopic: SubtopicMemory,
        participants: Sequence[Participant],
    ) -> SubtopicProgressReview:
        """
        Review current progress of the active subtopic.

        Args:
            host: Host actor responsible for orchestration.
            session: Parent topic session state.
            subtopic: Current active subtopic memory/state.
            participants: Participants relevant to the current subtopic.

        Returns:
            SubtopicProgressReview describing current progress status.
        """
        return self.host_controller.review_subtopic_progress(
            host=host,
            session=session,
            subtopic=subtopic,
            participants=participants,
        )

    def decide_continue_or_close_subtopic(
        self,
        host: Host,
        session: TopicSessionState,
        subtopic: SubtopicMemory,
        participants: Sequence[Participant],
    ) -> SubtopicControlDecision:
        """
        Decide whether the current subtopic should continue or close.

        Args:
            host: Host actor responsible for orchestration.
            session: Parent topic session state.
            subtopic: Current active subtopic memory/state.
            participants: Participants relevant to the current subtopic.

        Returns:
            SubtopicControlDecision describing the next subtopic-level
            control action.
        """
        return self.host_controller.decide_continue_or_close_subtopic(
            host=host,
            session=session,
            subtopic=subtopic,
            participants=participants,
        )

    def decide_next_speaker(
        self,
        host: Host,
        session: TopicSessionState,
        subtopic: SubtopicMemory,
        candidates: Sequence[Participant],
    ) -> SpeakerDecision:
        """
        Decide which participant should speak next.

        Args:
            host: Host actor responsible for orchestration.
            session: Parent topic session state.
            subtopic: Current active subtopic memory/state.
            candidates: Candidate participants for the next turn.

        Returns:
            SpeakerDecision describing the next turn-level selection.
        """
        return self.host_controller.decide_next_speaker(
            host=host,
            session=session,
            subtopic=subtopic,
            candidates=candidates,
        )
