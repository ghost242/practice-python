"""
Application entrypoint for integrating topic, subtopic, and turn runners.

This module wires the full discussion system together. It creates the host and
participant actors, provides simple runtime implementations for host and
participant behavior, constructs each runner layer, and executes one topic
session from the application entrypoint.

The integration order is:

1. Create actors and runtime adapters.
2. Construct the turn runner.
3. Construct the subtopic runner.
4. Construct the topic runner.
5. Execute one topic session from main().
"""

from __future__ import annotations

from typing import Sequence

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
from practice_files.practice_ml.discussion.models import (
    Host,
    Participant,
    ParticipantStatus,
    SubtopicMemory,
    SubtopicStatus,
    TopicSessionState,
    TopicStatus,
    UserParticipant,
)
from practice_files.practice_ml.discussion.participant.interface import (
    GeneratedTurnMessage,
    SpeakingParticipantInterface,
    TurnContext,
)
from practice_files.practice_ml.discussion.subtopic.interface import (
    SubtopicRunnerInterface,
)
from practice_files.practice_ml.discussion.subtopic.runner import (
    SubtopicRunner,
)
from practice_files.practice_ml.discussion.topic.dto import RunTopicInput
from practice_files.practice_ml.discussion.topic.interface import (
    TopicRunnerInterface,
)
from practice_files.practice_ml.discussion.topic.runner import TopicRunner
from practice_files.practice_ml.discussion.turn.interface import (
    TurnRunnerInterface,
)
from practice_files.practice_ml.discussion.turn.runner import TurnRunner


class SimpleHostRuntime(HostInterface):
    """
    Simple host runtime for end-to-end integration testing.

    This implementation is intentionally deterministic and minimal. It is not
    intended to be an intelligent discussion policy. Its purpose is to provide
    a concrete runtime that satisfies the host interfaces required by the
    runners.
    """

    def initialize_topic(
        self,
        host: Host,
        topic_input: TopicInput,
    ) -> TopicInitializationResult:
        """
        Initialize a topic session state from application topic input.

        Args:
            host:
                Host controller instance.
            topic_input:
                Topic input provided by the application.

        Returns:
            TopicInitializationResult:
                Initialized topic session state.
        """
        _ = host

        session = TopicSessionState(
            topic_id=topic_input.topic_id,
            title=topic_input.title,
            goal=topic_input.goal,
            status=TopicStatus.PENDING,
            turn_count=0,
            max_turns=topic_input.max_turns,
            opened_subtopic_count=0,
            closed_subtopic_count=0,
            subtopics=[],
            close_reason="",
        )
        return TopicInitializationResult(session=session)

    def define_topic_progress(
        self,
        host: Host,
        session: TopicSessionState,
    ) -> TopicProgressDefinitionResult:
        """
        Define topic progress as a fixed sequence of subtopics.

        Args:
            host:
                Host controller instance.
            session:
                Current topic session state.

        Returns:
            TopicProgressDefinitionResult:
                Planned subtopics for the topic.
        """
        _ = host
        _ = session

        return TopicProgressDefinitionResult(
            subtopics=[
                SubtopicPlan(
                    subtopic_id="subtopic-1",
                    title="Problem Framing",
                    description="Clarify the core problem and scope.",
                    achievement="A shared understanding of the problem.",
                ),
                SubtopicPlan(
                    subtopic_id="subtopic-2",
                    title="Option Analysis",
                    description="Compare candidate approaches.",
                    achievement="A reasoned comparison of options.",
                ),
                SubtopicPlan(
                    subtopic_id="subtopic-3",
                    title="Conclusion",
                    description="Synthesize the discussion and close.",
                    achievement="A concise final conclusion.",
                ),
            ]
        )

    def decide_next_subtopic(
        self,
        host: Host,
        session: TopicSessionState,
    ) -> NextSubtopicDecision:
        """
        Choose the next unopened subtopic.

        Args:
            host:
                Host controller instance.
            session:
                Current topic session state.

        Returns:
            NextSubtopicDecision:
                Next subtopic decision for the topic loop.
        """
        _ = host

        closed_ids = {
            subtopic.subtopic_id
            for subtopic in session.subtopics
            if subtopic.status
            in {SubtopicStatus.CLOSED, SubtopicStatus.FAILED}
        }

        planned_order = [
            (
                "subtopic-1",
                "Problem Framing",
                "Clarify the core problem and scope.",
                "A shared understanding of the problem.",
            ),
            (
                "subtopic-2",
                "Option Analysis",
                "Compare candidate approaches.",
                "A reasoned comparison of options.",
            ),
            (
                "subtopic-3",
                "Conclusion",
                "Synthesize the discussion and close.",
                "A concise final conclusion.",
            ),
        ]

        for subtopic_id, title, description, achievement in planned_order:
            if subtopic_id not in closed_ids:
                return NextSubtopicDecision(
                    should_close_topic=False,
                    close_reason="",
                    next_subtopic=SubtopicPlan(
                        subtopic_id=subtopic_id,
                        title=title,
                        description=description,
                        achievement=achievement,
                    ),
                )

        return NextSubtopicDecision(
            should_close_topic=True,
            close_reason="All planned subtopics have been completed.",
            next_subtopic=None,
        )

    def initialize_subtopic(
        self,
        host: Host,
        session: TopicSessionState,
        subtopic_plan: SubtopicPlan,
    ) -> SubtopicInitializationResult:
        """
        Initialize a subtopic runtime state from a subtopic plan.

        Args:
            host:
                Host controller instance.
            session:
                Current topic session state.
            subtopic_plan:
                Planned subtopic definition.

        Returns:
            SubtopicInitializationResult:
                Initialized subtopic runtime state.
        """
        _ = host
        _ = session

        subtopic = SubtopicMemory(
            subtopic_id=subtopic_plan.subtopic_id,
            title=subtopic_plan.title,
            description=subtopic_plan.description,
            achievement=subtopic_plan.achievement,
            status=SubtopicStatus.PENDING,
            is_active=False,
            turn_count=0,
            summary_text="",
            turns=[],
        )
        return SubtopicInitializationResult(subtopic=subtopic)

    def review_subtopic_progress(
        self,
        host: Host,
        session: TopicSessionState,
        subtopic: SubtopicMemory,
        participants: Sequence[Participant],
    ) -> SubtopicProgressReview:
        """
        Review current progress in the active subtopic.

        Args:
            host:
                Host controller instance.
            session:
                Current topic session state.
            subtopic:
                Current active subtopic.
            participants:
                Current participant collection.

        Returns:
            SubtopicProgressReview:
                Simple progress review.
        """
        _ = host
        _ = session
        _ = participants

        if subtopic.turn_count == 0:
            return SubtopicProgressReview(
                is_progressing=True,
                reason="Subtopic has just started.",
                missing_points=[],
            )

        if subtopic.turn_count < 2:
            return SubtopicProgressReview(
                is_progressing=True,
                reason="More discussion is useful before closure.",
                missing_points=[
                    "Need at least one more turn for development."
                ],
            )

        return SubtopicProgressReview(
            is_progressing=True,
            reason="Sufficient progress has been made.",
            missing_points=[],
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
            host:
                Host controller instance.
            session:
                Current topic session state.
            subtopic:
                Current active subtopic.
            participants:
                Current participant collection.

        Returns:
            SubtopicControlDecision:
                Continue-or-close decision for the subtopic loop.
        """
        _ = host
        _ = session
        _ = participants

        if subtopic.turn_count >= 2:
            return SubtopicControlDecision(
                should_continue=False,
                should_close=True,
                close_reason="Subtopic reached the target number of turns.",
            )

        return SubtopicControlDecision(
            should_continue=True,
            should_close=False,
            close_reason="",
        )

    def decide_next_speaker(
        self,
        host: Host,
        session: TopicSessionState,
        subtopic: SubtopicMemory,
        candidates: Sequence[Participant],
    ) -> SpeakerDecision:
        """
        Select the next speaker for the current turn.

        Args:
            host:
                Host controller instance.
            session:
                Current topic session state.
            subtopic:
                Current active subtopic.
            candidates:
                Selectable speaking actors.

        Returns:
            SpeakerDecision:
                Selected actor decision.
        """
        _ = host
        _ = session
        _ = subtopic

        available = [
            candidate
            for candidate in candidates
            if candidate.can_speak
            and candidate.participation_status != ParticipantStatus.FINISHED
        ]

        if not available:
            return SpeakerDecision(
                selected_actor_id=None,
                rationale="No available speaking actors.",
                host_message="No participant is currently available to speak.",
            )

        # Very simple rotation: choose the actor with the oldest latest_turn_index.
        selected = sorted(
            available,
            key=lambda item: (
                item.latest_turn_index
                if item.latest_turn_index is not None
                else -1
            ),
        )[0]

        return SpeakerDecision(
            selected_actor_id=selected.actor_id,
            rationale=f"Selected {selected.display_name} for the next contribution.",
            host_message="",
        )


class SimpleParticipantRuntime(SpeakingParticipantInterface):
    """
    Simple speaking runtime for participant and user actors.

    This implementation returns deterministic text suitable for integration
    testing and structural verification of the runner stack.
    """

    def produce_turn_message(
        self,
        participant: Participant | UserParticipant,
        session: TopicSessionState,
        subtopic: SubtopicMemory,
        turn_context: TurnContext,
    ) -> GeneratedTurnMessage:
        """
        Produce one message for the selected actor.

        Args:
            participant:
                Selected speaking actor.
            session:
                Current topic session state.
            subtopic:
                Current active subtopic.
            turn_context:
                Fresh turn context built by the turn layer.

        Returns:
            GeneratedTurnMessage:
                Produced message payload.
        """
        actor_kind = (
            "human user"
            if isinstance(participant, UserParticipant)
            else "participant"
        )

        content = (
            f"[{participant.display_name}] "
            f"As {actor_kind} in subtopic '{subtopic.title}', "
            f"I contribute to topic '{session.title}' on turn {turn_context.turn_index}."
        )

        return GeneratedTurnMessage(
            actor_id=participant.actor_id,
            content=content,
            metadata={
                "topic_id": session.topic_id,
                "subtopic_id": subtopic.subtopic_id,
            },
        )


def create_actors() -> tuple[
    Host,
    list[Participant],
    HostInterface,
    SpeakingParticipantInterface,
]:
    """
    Create discussion actors and runtime adapters.

    Returns:
        tuple[Host, list[Participant], HostInterface, SpeakingParticipantInterface]:
            Host instance, participant collection, host runtime implementation,
            and participant runtime implementation.
    """
    host = Host(
        actor_id="host-1",
        display_name="Host",
        description="Controls topic, subtopic, and turn flow.",
        system_prompt="Coordinate the discussion process.",
        authority_note="Session controller.",
    )

    participants: list[Participant] = [
        Participant(
            actor_id="participant-1",
            display_name="Olivia",
            description="Analytical participant.",
            role="System Architect",
            prompt="Focus on architecture and system structure.",
            base_knowledge=[
                "Distributed systems",
                "System design",
            ],
            goals=[
                "Clarify architecture trade-offs",
                "Contribute to structured conclusions",
            ],
            participation_status=ParticipantStatus.ONGOING,
        ),
        Participant(
            actor_id="participant-2",
            display_name="Ethan",
            description="Delivery-focused participant.",
            role="Backend Engineer",
            prompt="Focus on implementation and practicality.",
            base_knowledge=[
                "Backend systems",
                "Python services",
            ],
            goals=[
                "Identify implementable solutions",
                "Reduce system ambiguity",
            ],
            participation_status=ParticipantStatus.ONGOING,
        ),
        UserParticipant(
            actor_id="user-1",
            display_name="Jeffrey",
            description="Human participant.",
            role="User",
            prompt="Provide human input when selected.",
            base_knowledge=[],
            goals=["Provide constraints and intent."],
            participation_status=ParticipantStatus.ONGOING,
            user_external_id="local-user",
            is_human_input_required=False,
        ),
    ]

    host_runtime = SimpleHostRuntime()
    participant_runtime = SimpleParticipantRuntime()

    return host, participants, host_runtime, participant_runtime


def create_runners(
    *,
    host: Host,
    host_runtime: HostInterface,
    participant_runtime: SpeakingParticipantInterface,
) -> tuple[TurnRunnerInterface, SubtopicRunnerInterface, TopicRunnerInterface]:
    """
    Create and wire all runner layers.

    Args:
        host:
            Host controller instance.
        host_runtime:
            Host runtime implementation.
        participant_runtime:
            Participant speaking runtime implementation.

    Returns:
        tuple[TurnRunnerInterface, SubtopicRunnerInterface, TopicRunnerInterface]:
            Initialized turn, subtopic, and topic runners.
    """
    turn_runner = TurnRunner(
        host=host,
        host_runtime=host_runtime,
        participant_runtime=participant_runtime,
    )

    subtopic_runner = SubtopicRunner(
        host=host,
        host_runtime=host_runtime,
        turn_runner=turn_runner,
    )

    topic_runner = TopicRunner(
        host=host,
        host_runtime=host_runtime,
        subtopic_runner=subtopic_runner,
    )

    return turn_runner, subtopic_runner, topic_runner


def main() -> None:
    """
    Build the discussion system and execute one topic session.
    """
    host, participants, host_runtime, participant_runtime = create_actors()
    _, _, topic_runner = create_runners(
        host=host,
        host_runtime=host_runtime,
        participant_runtime=participant_runtime,
    )

    result = topic_runner.run_one_topic(
        RunTopicInput(
            topic_input=TopicInput(
                topic_id="topic-001",
                title="Design a multi-layer discussion orchestration system",
                goal=(
                    "Coordinate a topic through subtopics and turns under host control."
                ),
                max_turns=10,
            ),
            participants=participants,
        )
    )

    print(result.model_dump(mode="json", exclude_none=True))


if __name__ == "__main__":
    main()
