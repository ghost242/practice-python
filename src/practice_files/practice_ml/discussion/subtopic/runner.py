"""
Subtopic session runner.

This module defines the procedural entry point for executing one subtopic
session. The runner coordinates the subtopic workflow in a fixed sequence:

1. Validate input state.
2. Initialize the subtopic through the host.
3. Apply subtopic-open transition.
4. Repeatedly execute turn processing.
5. Rebuild subtopic control context after each turn.
6. Review progress and decide whether to continue or close.
7. Apply subtopic-close transition and return the final result.

The runner delegates specialized behavior to validation, service, turn, and
transition modules.
"""

from __future__ import annotations

from practice_files.practice_ml.discussion.models import Host
from practice_files.practice_ml.discussion.host.interface import HostInterface
from practice_files.practice_ml.discussion.participant.interface import (
    SpeakingParticipantInterface,
)
from practice_files.practice_ml.discussion.subtopic.dto import (
    CompletedSubtopicData,
    RunSubtopicInput,
    SubtopicRunResult,
    SubtopicTerminationReason,
)
from practice_files.practice_ml.discussion.subtopic.services import (
    evaluate_subtopic_control_cycle,
    initialize_subtopic,
    should_stop_subtopic_after_turn,
)
from practice_files.practice_ml.discussion.subtopic.transitions import (
    apply_close_subtopic_transition,
    apply_open_subtopic_transition,
)
from practice_files.practice_ml.discussion.subtopic.validators import (
    validate_initialized_subtopic,
    validate_participants,
    validate_run_subtopic_input,
    validate_subtopic_run_result,
)
from practice_files.practice_ml.discussion.turn.dto import PrepareTurnInput
from practice_files.practice_ml.discussion.turn.interface import (
    TurnRunnerInterface,
)


class SubtopicRunner:
    """
    Execute one subtopic session within an active topic session.

    The subtopic runner owns the focused discussion loop for a single
    subtopic. It does not decide which subtopic to run next; that belongs
    to the topic layer. It does not decide who speaks on each turn; that
    belongs to the turn layer under host control.
    """

    def __init__(
        self,
        *,
        host: Host,
        host_runtime: HostInterface,
        turn_runner: TurnRunnerInterface,
    ) -> None:
        """
        Initialize the subtopic runner with injected runtimes.

        Args:
            host:
                Host controller instance for the discussion session.
            host_runtime:
                Runtime implementation of host topic/subtopic control behavior.
            turn_runner:
                Turn runner used to execute one turn inside the subtopic loop.
        """
        self.host = host
        self.host_runtime = host_runtime
        self.turn_runner = turn_runner

    def run_one_subtopic(
        self,
        data: RunSubtopicInput,
    ) -> SubtopicRunResult:
        """
        Execute one subtopic session and commit subtopic state transitions.

        Args:
            data:
                Current topic session, selected subtopic plan, and participant
                collection for one subtopic session.

        Returns:
            SubtopicRunResult:
                Structured result of the executed subtopic session.
        """
        try:
            validate_run_subtopic_input(data)
            validate_participants(data.participants)
        except Exception as exc:
            result = SubtopicRunResult(
                reason=SubtopicTerminationReason.VALIDATION_FAILED,
                subtopic_id=(
                    data.subtopic_plan.subtopic_id
                    if data.subtopic_plan
                    else ""
                ),
                subtopic_title=(
                    data.subtopic_plan.title if data.subtopic_plan else ""
                ),
                error_message=str(exc),
            )
            validate_subtopic_run_result(result)
            return result

        try:
            initialized = initialize_subtopic(
                host_runtime=self.host_runtime,
                host=self.host,
                session=data.session,
                subtopic_plan=data.subtopic_plan,
            )
            validate_initialized_subtopic(initialized.subtopic)
        except Exception as exc:
            result = SubtopicRunResult(
                reason=SubtopicTerminationReason.FAILED,
                subtopic_id=data.subtopic_plan.subtopic_id,
                subtopic_title=data.subtopic_plan.title,
                error_message=f"Failed to initialize subtopic: {exc}",
            )
            validate_subtopic_run_result(result)
            return result

        subtopic = initialized.subtopic
        apply_open_subtopic_transition(
            session=data.session,
            subtopic=subtopic,
        )

        turn_results = []
        final_progress_review = None
        final_control_decision = None

        try:
            while True:
                if (
                    data.max_turns > 0
                    and subtopic.turn_count >= data.max_turns
                ):
                    completed = CompletedSubtopicData(
                        subtopic=subtopic,
                        final_progress_review=final_progress_review,
                        final_control_decision=final_control_decision,
                    )
                    result = SubtopicRunResult(
                        reason=SubtopicTerminationReason.TURN_LIMIT_REACHED,
                        subtopic_id=subtopic.subtopic_id,
                        subtopic_title=subtopic.title,
                        turn_results=list(turn_results),
                        final_progress_review=final_progress_review,
                        final_control_decision=final_control_decision,
                        completed=completed,
                    )
                    apply_close_subtopic_transition(
                        session=data.session,
                        subtopic=subtopic,
                        result=result,
                    )
                    validate_subtopic_run_result(result)
                    return result

                turn_input = PrepareTurnInput(
                    session=data.session,
                    subtopic=subtopic,
                    participants=data.participants,
                )

                turn_result = self.turn_runner.run_one_turn(turn_input)
                turn_results.append(turn_result)

                if should_stop_subtopic_after_turn(turn_result):
                    result = SubtopicRunResult(
                        reason=SubtopicTerminationReason.TURN_FAILED,
                        subtopic_id=subtopic.subtopic_id,
                        subtopic_title=subtopic.title,
                        turn_results=list(turn_results),
                        final_progress_review=final_progress_review,
                        final_control_decision=final_control_decision,
                        error_message=turn_result.error_message,
                    )
                    apply_close_subtopic_transition(
                        session=data.session,
                        subtopic=subtopic,
                        result=result,
                    )
                    validate_subtopic_run_result(result)
                    return result

                _, continue_decision = evaluate_subtopic_control_cycle(
                    host_runtime=self.host_runtime,
                    host=self.host,
                    session=data.session,
                    subtopic=subtopic,
                    participants=data.participants,
                    recent_turn_results=turn_results,
                )

                final_progress_review = continue_decision.progress_review
                final_control_decision = continue_decision.control_decision

                if continue_decision.should_close_subtopic:
                    reason = SubtopicTerminationReason.HOST_REQUESTED_CLOSE
                    if (
                        final_control_decision is not None
                        and not final_control_decision.close_reason
                    ):
                        reason = SubtopicTerminationReason.COMPLETED

                    completed = CompletedSubtopicData(
                        subtopic=subtopic,
                        final_progress_review=final_progress_review,
                        final_control_decision=final_control_decision,
                    )
                    result = SubtopicRunResult(
                        reason=reason,
                        subtopic_id=subtopic.subtopic_id,
                        subtopic_title=subtopic.title,
                        turn_results=list(turn_results),
                        final_progress_review=final_progress_review,
                        final_control_decision=final_control_decision,
                        completed=completed,
                    )
                    apply_close_subtopic_transition(
                        session=data.session,
                        subtopic=subtopic,
                        result=result,
                    )
                    validate_subtopic_run_result(result)
                    return result

                if not continue_decision.should_continue_turn_loop:
                    completed = CompletedSubtopicData(
                        subtopic=subtopic,
                        final_progress_review=final_progress_review,
                        final_control_decision=final_control_decision,
                    )
                    result = SubtopicRunResult(
                        reason=SubtopicTerminationReason.COMPLETED,
                        subtopic_id=subtopic.subtopic_id,
                        subtopic_title=subtopic.title,
                        turn_results=list(turn_results),
                        final_progress_review=final_progress_review,
                        final_control_decision=final_control_decision,
                        completed=completed,
                    )
                    apply_close_subtopic_transition(
                        session=data.session,
                        subtopic=subtopic,
                        result=result,
                    )
                    validate_subtopic_run_result(result)
                    return result

        except Exception as exc:
            result = SubtopicRunResult(
                reason=SubtopicTerminationReason.FAILED,
                subtopic_id=subtopic.subtopic_id,
                subtopic_title=subtopic.title,
                turn_results=list(turn_results),
                final_progress_review=final_progress_review,
                final_control_decision=final_control_decision,
                error_message=str(exc),
            )
            apply_close_subtopic_transition(
                session=data.session,
                subtopic=subtopic,
                result=result,
            )
            validate_subtopic_run_result(result)
            return result
