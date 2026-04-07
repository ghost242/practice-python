"""
Topic coordination services.

This module implements pure orchestration logic for one topic session. It
coordinates host-controlled topic initialization, progress definition,
next-subtopic selection, and interpretation of subtopic outcomes without
mutating runtime state.

Responsibilities include:
- Requesting topic initialization from the host.
- Requesting topic progress definition as subtopics.
- Requesting next-subtopic selection from the host.
- Building normalized topic loop control decisions.
- Translating subtopic-level outcomes into topic-level control signals.

State mutation is intentionally excluded and delegated to the transition layer.
"""

from __future__ import annotations

from practice_files.practice_ml.discussion.host.interface import (
    HostInterface,
    TopicInput,
    TopicProgressDefinitionResult,
)
from practice_files.practice_ml.discussion.models import (
    Host,
    Participant,
    TopicSessionState,
)
from practice_files.practice_ml.discussion.subtopic.dto import (
    SubtopicRunResult,
    SubtopicTerminationReason,
)
from practice_files.practice_ml.discussion.topic.context import (
    prepare_topic_context,
)
from practice_files.practice_ml.discussion.topic.dto import (
    ContinueTopicDecision,
    InitializeTopicResult,
    TopicContext,
)


def initialize_topic(
    *,
    host_runtime: HostInterface,
    host: Host,
    topic_input: TopicInput,
) -> InitializeTopicResult:
    """
    Request topic initialization from the host.

    Args:
        host_runtime:
            Host runtime implementation.
        host:
            Host controller instance.
        topic_input:
            Topic input provided by the application layer.

    Returns:
        InitializeTopicResult:
            Initialized mutable topic session state.
    """
    result = host_runtime.initialize_topic(
        host=host,
        topic_input=topic_input,
    )
    return InitializeTopicResult(session=result.session)


def define_topic_progress(
    *,
    host_runtime: HostInterface,
    host: Host,
    session: TopicSessionState,
) -> TopicProgressDefinitionResult:
    """
    Request topic progress definition from the host.

    Args:
        host_runtime:
            Host runtime implementation.
        host:
            Host controller instance.
        session:
            Current topic session state.

    Returns:
        TopicProgressDefinitionResult:
            Host-produced progress definition as subtopics.
    """
    return host_runtime.define_topic_progress(
        host=host,
        session=session,
    )


def decide_next_subtopic(
    *,
    host_runtime: HostInterface,
    host: Host,
    session: TopicSessionState,
):
    """
    Request next-subtopic selection from the host.

    Args:
        host_runtime:
            Host runtime implementation.
        host:
            Host controller instance.
        session:
            Current topic session state.

    Returns:
        NextSubtopicDecision:
            Host-produced next-subtopic decision.
    """
    return host_runtime.decide_next_subtopic(
        host=host,
        session=session,
    )


def build_continue_topic_decision(
    *,
    next_subtopic_decision,
) -> ContinueTopicDecision:
    """
    Normalize host next-subtopic output into one runner-facing topic decision.

    Args:
        next_subtopic_decision:
            Host-produced next-subtopic decision.

    Returns:
        ContinueTopicDecision:
            Normalized control decision for the next topic loop step.
    """
    should_close = bool(next_subtopic_decision.should_close_topic)
    has_next_subtopic = next_subtopic_decision.next_subtopic is not None
    should_continue = has_next_subtopic and not should_close

    return ContinueTopicDecision(
        should_continue_topic_loop=should_continue,
        should_close_topic=should_close or not has_next_subtopic,
        reason=next_subtopic_decision.close_reason,
        next_subtopic_decision=next_subtopic_decision,
    )


def evaluate_topic_control_cycle(
    *,
    host_runtime: HostInterface,
    host: Host,
    session: TopicSessionState,
    participants: list[Participant],
    subtopic_results: list[SubtopicRunResult] | None = None,
) -> tuple[TopicContext, ContinueTopicDecision]:
    """
    Execute one topic control cycle.

    This function rebuilds fresh topic context, asks the host which subtopic
    should run next or whether the topic should close, and normalizes the
    result into one control decision.

    Args:
        host_runtime:
            Host runtime implementation.
        host:
            Host controller instance.
        session:
            Current topic session state.
        participants:
            Current participant collection.
        subtopic_results:
            Subtopic results observed so far during the topic loop.

    Returns:
        tuple[TopicContext, ContinueTopicDecision]:
            Fresh topic context and normalized loop control decision.
    """
    prepared = prepare_topic_context(
        session=session,
        participants=participants,
        subtopic_results=subtopic_results,
    )

    next_subtopic_decision = decide_next_subtopic(
        host_runtime=host_runtime,
        host=host,
        session=session,
    )

    normalized = build_continue_topic_decision(
        next_subtopic_decision=next_subtopic_decision,
    )

    return prepared.context, normalized


def should_stop_topic_after_subtopic(
    subtopic_result: SubtopicRunResult,
) -> bool:
    """
    Determine whether a subtopic result should force topic termination.

    Args:
        subtopic_result:
            Result of one executed subtopic session.

    Returns:
        bool:
            True if the topic runner should treat this subtopic result as a
            structural stop condition.
    """
    return subtopic_result.reason in {
        SubtopicTerminationReason.FAILED,
        SubtopicTerminationReason.VALIDATION_FAILED,
        SubtopicTerminationReason.TURN_FAILED,
    }
