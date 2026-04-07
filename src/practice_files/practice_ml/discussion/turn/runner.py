"""
Turn execution runner.

This module defines the procedural entry point for executing one turn. The
runner coordinates the full turn workflow in a fixed sequence:

1. Validate input state.
2. Build a fresh turn context.
3. Execute coordination logic between host and speaker.
4. Validate the result.
5. Apply state transition if the turn completes successfully.

The runner delegates all specialized behavior to context, service, validator,
and transition modules.
"""

from __future__ import annotations

from practice_files.practice_ml.discussion.models import Host
from practice_files.practice_ml.discussion.host.interface import HostInterface
from practice_files.practice_ml.discussion.participant.interface import (
    SpeakingParticipantInterface,
)
from practice_files.practice_ml.discussion.turn.context import (
    build_turn_context,
)
from practice_files.practice_ml.discussion.turn.dto import (
    PrepareTurnInput,
    TurnProcessResult,
)
from practice_files.practice_ml.discussion.turn.services import (
    execute_turn_process,
)
from practice_files.practice_ml.discussion.turn.transitions import (
    apply_turn_transition,
)
from practice_files.practice_ml.discussion.turn.validators import (
    validate_participants,
    validate_prepare_turn_input,
    validate_turn_process_result,
)


class TurnRunner:
    """
    Execute one turn process within an active subtopic session.

    This runner coordinates the turn package workflow in a fixed order:

    1. validate current input state
    2. build a fresh turn context
    3. execute pure turn coordination logic
    4. validate the produced result
    5. apply state transition only if the turn completed successfully

    The runner does not contain host strategy or participant generation logic.
    Those behaviors are injected through the host and participant interfaces.
    """

    def __init__(
        self,
        *,
        host: Host,
        host_runtime: HostInterface,
        participant_runtime: SpeakingParticipantInterface,
    ) -> None:
        """
        Initialize the turn runner with injected actor runtimes.

        Args:
            host:
                Host controller instance for the session.
            host_runtime:
                Runtime implementation of host decision behavior.
            participant_runtime:
                Runtime implementation of speaking behavior for participants
                and user participants.
        """
        self.host = host
        self.host_runtime = host_runtime
        self.participant_runtime = participant_runtime

    def run_one_turn(
        self,
        data: PrepareTurnInput,
    ) -> TurnProcessResult:
        """
        Execute one turn attempt and commit state mutation on success.

        Args:
            data:
                Current session, active subtopic, and selectable participants.

        Returns:
            TurnProcessResult:
                Structured outcome of the turn execution attempt.
        """
        validate_prepare_turn_input(data)
        validate_participants(data.participants)

        turn_context = build_turn_context(
            session=data.session,
            subtopic=data.subtopic,
            participants=data.participants,
        )

        result = execute_turn_process(
            host_runtime=self.host_runtime,
            host=self.host,
            participant_runtime=self.participant_runtime,
            session=data.session,
            subtopic=data.subtopic,
            participants=data.participants,
            turn_context=turn_context,
        )

        validate_turn_process_result(result)

        if result.is_completed:
            apply_turn_transition(
                session=data.session,
                subtopic=data.subtopic,
                participants=data.participants,
                completed=result.completed,
            )

        return result
