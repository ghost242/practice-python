from __future__ import annotations

from practice_files.practice_ml.discussion.agent_runtime.interface import (
    StructuredAgentRuntime,
)
from practice_files.practice_ml.discussion.participant.interface import (
    ParticipantInterface,
)
from practice_files.practice_ml.discussion.participant.dto import (
    ParticipantReplyDecision,
    ParticipantSummaryDecision,
    ParticipantEvaluationDecision,
)
from practice_files.practice_ml.discussion.participant.prompts import (
    build_reply_prompt,
    build_summary_prompt,
    build_evaluation_prompt,
)


class LlmParticipantAgent(ParticipantInterface):
    """
    Participant implementation backed by the shared agent runtime.
    """

    def __init__(self, runtime: StructuredAgentRuntime) -> None:
        self._runtime = runtime

    def generate_reply(self, participant, context) -> ParticipantReplyDecision:
        system_prompt, user_prompt = build_reply_prompt(
            participant=participant,
            context=context,
        )
        return self._runtime.invoke_structured(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            response_model=ParticipantReplyDecision,
        )

    def summarize_contribution(
        self, participant, context
    ) -> ParticipantSummaryDecision:
        system_prompt, user_prompt = build_summary_prompt(
            participant=participant,
            context=context,
        )
        return self._runtime.invoke_structured(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            response_model=ParticipantSummaryDecision,
        )

    def evaluate_progress(
        self, participant, context
    ) -> ParticipantEvaluationDecision:
        system_prompt, user_prompt = build_evaluation_prompt(
            participant=participant,
            context=context,
        )
        return self._runtime.invoke_structured(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            response_model=ParticipantEvaluationDecision,
        )
