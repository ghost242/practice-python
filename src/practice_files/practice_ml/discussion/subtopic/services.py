"""
Subtopic coordination services.

This module implements pure orchestration logic for one subtopic session. It
coordinates host-controlled subtopic initialization, progress review,
continue-or-close decisions, and interpretation of turn outcomes without
mutating runtime state.

Responsibilities include:
- Requesting subtopic initialization from the host.
- Building normalized subtopic control decisions.
- Reviewing progress after turn execution.
- Deciding whether the subtopic loop should continue or close.
- Translating turn-level outcomes into subtopic-level control signals.

State mutation is intentionally excluded and delegated to the transition layer.
"""

from __future__ import annotations

from practice_files.practice_ml.discussion.host.interface import (
    HostInterface,
    SubtopicPlan,
)
from practice_files.practice_ml.discussion.models import (
    Host,
    Participant,
    SubtopicMemory,
    TopicSessionState,
)
from practice_files.practice_ml.discussion.subtopic.context import (
    prepare_subtopic_context,
)
from practice_files.practice_ml.discussion.subtopic.dto import (
    ContinueSubtopicDecision,
    InitializeSubtopicResult,
    SubtopicContext,
)
from practice_files.practice_ml.discussion.turn.dto import (
    TurnProcessResult,
    TurnTerminationReason,
)


def initialize_subtopic(
    *,
    host_runtime: HostInterface,
    host: Host,
    session: TopicSessionState,
    subtopic_plan: SubtopicPlan,
) -> InitializeSubtopicResult:
    """
    Request subtopic initialization from the host.

    Args:
        host_runtime:
            Host runtime implementation.
        host:
            Host controller instance.
        session:
            Current topic session state.
        subtopic_plan:
            Planned subtopic definition selected by the topic layer.

    Returns:
        InitializeSubtopicResult:
            Initialized mutable subtopic state.
    """
    result = host_runtime.initialize_subtopic(
        host=host,
        session=session,
        subtopic_plan=subtopic_plan,
    )
    return InitializeSubtopicResult(subtopic=result.subtopic)


def review_subtopic_progress(
    *,
    host_runtime: HostInterface,
    host: Host,
    session: TopicSessionState,
    subtopic: SubtopicMemory,
    participants: list[Participant],
):
    """
    Request subtopic progress review from the host.

    Args:
        host_runtime:
            Host runtime implementation.
        host:
            Host controller instance.
        session:
            Current topic session state.
        subtopic:
            Current active subtopic state.
        participants:
            Current participant collection.

    Returns:
        SubtopicProgressReview:
            Host-produced review of current subtopic progress.
    """
    return host_runtime.review_subtopic_progress(
        host=host,
        session=session,
        subtopic=subtopic,
        participants=participants,
    )


def decide_continue_or_close_subtopic(
    *,
    host_runtime: HostInterface,
    host: Host,
    session: TopicSessionState,
    subtopic: SubtopicMemory,
    participants: list[Participant],
):
    """
    Request continue-or-close control decision from the host.

    Args:
        host_runtime:
            Host runtime implementation.
        host:
            Host controller instance.
        session:
            Current topic session state.
        subtopic:
            Current active subtopic state.
        participants:
            Current participant collection.

    Returns:
        SubtopicControlDecision:
            Host-produced control decision for the subtopic loop.
    """
    return host_runtime.decide_continue_or_close_subtopic(
        host=host,
        session=session,
        subtopic=subtopic,
        participants=participants,
    )


def build_continue_subtopic_decision(
    *,
    progress_review,
    control_decision,
) -> ContinueSubtopicDecision:
    """
    Normalize host review and control outputs into one runner-facing decision.

    Args:
        progress_review:
            Host progress review for the active subtopic.
        control_decision:
            Host continue-or-close decision.

    Returns:
        ContinueSubtopicDecision:
            Normalized control decision for the next subtopic loop step.
    """
    should_close = bool(control_decision.should_close)
    should_continue = (
        bool(control_decision.should_continue) and not should_close
    )

    reason_parts: list[str] = []

    if progress_review is not None and progress_review.reason:
        reason_parts.append(progress_review.reason)

    if control_decision is not None and control_decision.close_reason:
        reason_parts.append(control_decision.close_reason)

    return ContinueSubtopicDecision(
        should_continue_turn_loop=should_continue,
        should_close_subtopic=should_close,
        reason=" | ".join(reason_parts),
        progress_review=progress_review,
        control_decision=control_decision,
    )


def evaluate_subtopic_control_cycle(
    *,
    host_runtime: HostInterface,
    host: Host,
    session: TopicSessionState,
    subtopic: SubtopicMemory,
    participants: list[Participant],
    recent_turn_results: list[TurnProcessResult] | None = None,
) -> tuple[SubtopicContext, ContinueSubtopicDecision]:
    """
    Execute one subtopic control cycle.

    This function rebuilds fresh subtopic context, asks the host to review
    progress, asks the host whether the subtopic should continue or close, and
    then normalizes the result into one control decision.

    Args:
        host_runtime:
            Host runtime implementation.
        host:
            Host controller instance.
        session:
            Current topic session state.
        subtopic:
            Current active subtopic state.
        participants:
            Current participant collection.
        recent_turn_results:
            Recent turn results observed during the subtopic loop.

    Returns:
        tuple[SubtopicContext, ContinueSubtopicDecision]:
            Fresh subtopic context and normalized loop control decision.
    """
    prepared = prepare_subtopic_context(
        session=session,
        subtopic=subtopic,
        participants=participants,
        recent_turn_results=recent_turn_results,
    )

    progress_review = review_subtopic_progress(
        host_runtime=host_runtime,
        host=host,
        session=session,
        subtopic=subtopic,
        participants=participants,
    )

    control_decision = decide_continue_or_close_subtopic(
        host_runtime=host_runtime,
        host=host,
        session=session,
        subtopic=subtopic,
        participants=participants,
    )

    normalized = build_continue_subtopic_decision(
        progress_review=progress_review,
        control_decision=control_decision,
    )

    return prepared.context, normalized


def should_stop_subtopic_after_turn(
    turn_result: TurnProcessResult,
) -> bool:
    """
    Determine whether a turn result should force subtopic termination.

    Args:
        turn_result:
            Result of one executed turn.

    Returns:
        bool:
            True if the subtopic runner should treat this turn result as a
            structural stop condition.
    """
    return turn_result.reason in {
        TurnTerminationReason.FAILED,
    }
