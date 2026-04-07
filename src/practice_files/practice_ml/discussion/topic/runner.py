"""
Topic session runner.

This module defines the procedural entry point for executing one topic
session. The runner coordinates the topic workflow in a fixed sequence:

1. Validate input state.
2. Initialize the topic through the host.
3. Apply topic-open transition.
4. Define topic progress as subtopics.
5. Repeatedly evaluate topic control and execute subtopic sessions.
6. Apply topic-progress transition after each completed subtopic.
7. Apply topic-close transition and return the final result.

The runner delegates specialized behavior to validation, service, subtopic,
and transition modules.
"""

from __future__ import annotations

from practice_files.practice_ml.discussion.models import Host
from practice_files.practice_ml.discussion.host.interface import HostInterface
from practice_files.practice_ml.discussion.subtopic.interface import (
    SubtopicRunnerInterface,
)
from practice_files.practice_ml.discussion.topic.dto import (
    CompletedTopicData,
    RunTopicInput,
    TopicRunResult,
    TopicTerminationReason,
)
from practice_files.practice_ml.discussion.topic.services import (
    define_topic_progress,
    evaluate_topic_control_cycle,
    initialize_topic,
    should_stop_topic_after_subtopic,
)
from practice_files.practice_ml.discussion.topic.transitions import (
    apply_close_topic_transition,
    apply_open_topic_transition,
    apply_subtopic_result_transition,
    apply_topic_progress_definition,
)
from practice_files.practice_ml.discussion.topic.validators import (
    validate_initialized_topic_session,
    validate_participants,
    validate_run_topic_input,
    validate_topic_progress_definition,
    validate_topic_run_result,
)


class TopicRunner:
    """
    Execute one topic session across multiple subtopic sessions.

    The topic runner owns the outer discussion loop. It does not decide which
    actor speaks on a turn and does not execute turn logic directly. Instead,
    it delegates subtopic execution to the subtopic runner and uses host-driven
    control decisions to decide whether another subtopic should run.
    """

    def __init__(
        self,
        *,
        host: Host,
        host_runtime: HostInterface,
        subtopic_runner: SubtopicRunnerInterface,
    ) -> None:
        """
        Initialize the topic runner with injected runtimes.

        Args:
            host:
                Host controller instance for the discussion session.
            host_runtime:
                Runtime implementation of host topic control behavior.
            subtopic_runner:
                Subtopic runner used to execute one subtopic session inside the
                topic loop.
        """
        self.host = host
        self.host_runtime = host_runtime
        self.subtopic_runner = subtopic_runner

    def run_one_topic(
        self,
        data: RunTopicInput,
    ) -> TopicRunResult:
        """
        Execute one topic session and commit topic state transitions.

        Args:
            data:
                Topic input and current participant collection for one topic
                session.

        Returns:
            TopicRunResult:
                Structured result of the executed topic session.
        """
        try:
            validate_run_topic_input(data)
            validate_participants(data.participants)
        except Exception as exc:
            result = TopicRunResult(
                reason=TopicTerminationReason.VALIDATION_FAILED,
                topic_id=data.topic_input.topic_id if data.topic_input else "",
                topic_title=data.topic_input.title if data.topic_input else "",
                error_message=str(exc),
            )
            validate_topic_run_result(result)
            return result

        try:
            initialized = initialize_topic(
                host_runtime=self.host_runtime,
                host=self.host,
                topic_input=data.topic_input,
            )
            validate_initialized_topic_session(initialized.session)
        except Exception as exc:
            result = TopicRunResult(
                reason=TopicTerminationReason.FAILED,
                topic_id=data.topic_input.topic_id,
                topic_title=data.topic_input.title,
                error_message=f"Failed to initialize topic: {exc}",
            )
            validate_topic_run_result(result)
            return result

        session = initialized.session
        apply_open_topic_transition(session=session)

        try:
            progress_definition = define_topic_progress(
                host_runtime=self.host_runtime,
                host=self.host,
                session=session,
            )
            validate_topic_progress_definition(progress_definition)
            apply_topic_progress_definition(
                session=session,
                progress_definition=progress_definition,
            )
        except Exception as exc:
            result = TopicRunResult(
                reason=TopicTerminationReason.FAILED,
                topic_id=session.topic_id,
                topic_title=session.title,
                error_message=f"Failed to define topic progress: {exc}",
            )
            apply_close_topic_transition(
                session=session,
                result=result,
            )
            validate_topic_run_result(result)
            return result

        if not progress_definition.subtopics:
            completed = CompletedTopicData(
                session=session,
                final_next_subtopic_decision=None,
                progress_definition=progress_definition,
            )
            result = TopicRunResult(
                reason=TopicTerminationReason.NO_SUBTOPICS_DEFINED,
                topic_id=session.topic_id,
                topic_title=session.title,
                progress_definition=progress_definition,
                completed=completed,
            )
            apply_close_topic_transition(
                session=session,
                result=result,
            )
            validate_topic_run_result(result)
            return result

        subtopic_results = []
        final_next_subtopic_decision = None
        planned_subtopics_by_id = {
            subtopic.subtopic_id: subtopic
            for subtopic in progress_definition.subtopics
        }
        executed_subtopic_ids: set[str] = set()

        try:
            while True:
                _, continue_decision = evaluate_topic_control_cycle(
                    host_runtime=self.host_runtime,
                    host=self.host,
                    session=session,
                    participants=data.participants,
                    subtopic_results=subtopic_results,
                )

                final_next_subtopic_decision = (
                    continue_decision.next_subtopic_decision
                )

                if continue_decision.should_close_topic:
                    reason = TopicTerminationReason.HOST_REQUESTED_CLOSE
                    if (
                        final_next_subtopic_decision is not None
                        and not final_next_subtopic_decision.should_close_topic
                    ):
                        reason = TopicTerminationReason.COMPLETED
                    elif (
                        final_next_subtopic_decision is not None
                        and not final_next_subtopic_decision.close_reason
                    ):
                        reason = TopicTerminationReason.NO_MORE_SUBTOPICS

                    completed = CompletedTopicData(
                        session=session,
                        final_next_subtopic_decision=final_next_subtopic_decision,
                        progress_definition=progress_definition,
                    )
                    result = TopicRunResult(
                        reason=reason,
                        topic_id=session.topic_id,
                        topic_title=session.title,
                        progress_definition=progress_definition,
                        subtopic_results=list(subtopic_results),
                        final_next_subtopic_decision=final_next_subtopic_decision,
                        completed=completed,
                    )
                    apply_close_topic_transition(
                        session=session,
                        result=result,
                    )
                    validate_topic_run_result(result)
                    return result

                next_subtopic = (
                    final_next_subtopic_decision.next_subtopic
                    if final_next_subtopic_decision is not None
                    else None
                )

                if next_subtopic is None:
                    completed = CompletedTopicData(
                        session=session,
                        final_next_subtopic_decision=final_next_subtopic_decision,
                        progress_definition=progress_definition,
                    )
                    result = TopicRunResult(
                        reason=TopicTerminationReason.NO_MORE_SUBTOPICS,
                        topic_id=session.topic_id,
                        topic_title=session.title,
                        progress_definition=progress_definition,
                        subtopic_results=list(subtopic_results),
                        final_next_subtopic_decision=final_next_subtopic_decision,
                        completed=completed,
                    )
                    apply_close_topic_transition(
                        session=session,
                        result=result,
                    )
                    validate_topic_run_result(result)
                    return result

                if next_subtopic.subtopic_id in executed_subtopic_ids:
                    completed = CompletedTopicData(
                        session=session,
                        final_next_subtopic_decision=final_next_subtopic_decision,
                        progress_definition=progress_definition,
                    )
                    result = TopicRunResult(
                        reason=TopicTerminationReason.NO_MORE_SUBTOPICS,
                        topic_id=session.topic_id,
                        topic_title=session.title,
                        progress_definition=progress_definition,
                        subtopic_results=list(subtopic_results),
                        final_next_subtopic_decision=final_next_subtopic_decision,
                        completed=completed,
                    )
                    apply_close_topic_transition(
                        session=session,
                        result=result,
                    )
                    validate_topic_run_result(result)
                    return result

                planned_subtopic = planned_subtopics_by_id.get(
                    next_subtopic.subtopic_id, next_subtopic
                )

                subtopic_result = self.subtopic_runner.run_one_subtopic(
                    data=__import__(
                        "subtopic.dto", fromlist=["RunSubtopicInput"]
                    ).RunSubtopicInput(
                        session=session,
                        subtopic_plan=planned_subtopic,
                        participants=data.participants,
                        max_turns=session.max_turns,
                    )
                )
                subtopic_results.append(subtopic_result)
                executed_subtopic_ids.add(planned_subtopic.subtopic_id)

                apply_subtopic_result_transition(
                    session=session,
                    subtopic_result=subtopic_result,
                )

                if should_stop_topic_after_subtopic(subtopic_result):
                    result = TopicRunResult(
                        reason=TopicTerminationReason.SUBTOPIC_FAILED,
                        topic_id=session.topic_id,
                        topic_title=session.title,
                        progress_definition=progress_definition,
                        subtopic_results=list(subtopic_results),
                        final_next_subtopic_decision=final_next_subtopic_decision,
                        error_message=subtopic_result.error_message,
                    )
                    apply_close_topic_transition(
                        session=session,
                        result=result,
                    )
                    validate_topic_run_result(result)
                    return result

        except Exception as exc:
            result = TopicRunResult(
                reason=TopicTerminationReason.FAILED,
                topic_id=session.topic_id,
                topic_title=session.title,
                progress_definition=progress_definition,
                subtopic_results=list(subtopic_results),
                final_next_subtopic_decision=final_next_subtopic_decision,
                error_message=str(exc),
            )
            apply_close_topic_transition(
                session=session,
                result=result,
            )
            validate_topic_run_result(result)
            return result
