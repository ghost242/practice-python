from __future__ import annotations

from typing import Sequence

from practice_files.practice_ml.discussion.agent_runtime.interface import (
    StructuredAgentRuntime,
)
from practice_files.practice_ml.discussion.host.dto import (
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
from practice_files.practice_ml.discussion.host.interface import HostInterface
from practice_files.practice_ml.discussion.host.prompts import (
    build_decide_next_speaker_prompt,
    build_decide_next_subtopic_prompt,
    build_define_topic_progress_prompt,
    build_review_subtopic_progress_prompt,
    build_subtopic_control_prompt,
)
from practice_files.practice_ml.discussion.models import (
    Host,
    Participant,
    SubtopicMemory,
    TopicSessionState,
)


class LlmHostAgent(HostInterface):
    """
    Host controller implemented as an LLM-backed agent.
    """

    def __init__(self, runtime: StructuredAgentRuntime) -> None:
        self._runtime = runtime

    def initialize_topic(
        self,
        host: Host,
        topic_input: TopicInput,
    ) -> TopicInitializationResult:
        session = TopicSessionState(
            topic_id=topic_input.topic_id,
            title=topic_input.title,
            goal=topic_input.goal,
            max_turns=topic_input.max_turns,
            status="OPEN",
        )
        return TopicInitializationResult(session=session)

    def define_topic_progress(
        self,
        host: Host,
        session: TopicSessionState,
    ) -> TopicProgressDefinitionResult:
        system_prompt, user_prompt = build_define_topic_progress_prompt(
            host=host,
            session=session,
        )
        return self._runtime.invoke_structured(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            response_model=TopicProgressDefinitionResult,
        )

    def decide_next_subtopic(
        self,
        host: Host,
        session: TopicSessionState,
    ) -> NextSubtopicDecision:
        system_prompt, user_prompt = build_decide_next_subtopic_prompt(
            host=host,
            session=session,
        )
        return self._runtime.invoke_structured(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            response_model=NextSubtopicDecision,
        )

    def initialize_subtopic(
        self,
        host: Host,
        session: TopicSessionState,
        subtopic_plan: SubtopicPlan,
    ) -> SubtopicInitializationResult:
        subtopic = SubtopicMemory(
            subtopic_id=subtopic_plan.subtopic_id,
            title=subtopic_plan.title,
            description=subtopic_plan.description,
            achievement=subtopic_plan.achievement,
            status="OPEN",
        )
        return SubtopicInitializationResult(subtopic=subtopic)

    def review_subtopic_progress(
        self,
        host: Host,
        session: TopicSessionState,
        subtopic: SubtopicMemory,
        participants: Sequence[Participant],
    ) -> SubtopicProgressReview:
        system_prompt, user_prompt = build_review_subtopic_progress_prompt(
            host=host,
            session=session,
            subtopic=subtopic,
            participants=participants,
        )
        return self._runtime.invoke_structured(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            response_model=SubtopicProgressReview,
        )

    def decide_continue_or_close_subtopic(
        self,
        host: Host,
        session: TopicSessionState,
        subtopic: SubtopicMemory,
        participants: Sequence[Participant],
    ) -> SubtopicControlDecision:
        system_prompt, user_prompt = build_subtopic_control_prompt(
            host=host,
            session=session,
            subtopic=subtopic,
            participants=participants,
        )
        return self._runtime.invoke_structured(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            response_model=SubtopicControlDecision,
        )

    def decide_next_speaker(
        self,
        host: Host,
        session: TopicSessionState,
        subtopic: SubtopicMemory,
        candidates: Sequence[Participant],
    ) -> SpeakerDecision:
        system_prompt, user_prompt = build_decide_next_speaker_prompt(
            host=host,
            session=session,
            subtopic=subtopic,
            candidates=candidates,
        )
        return self._runtime.invoke_structured(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            response_model=SpeakerDecision,
        )
