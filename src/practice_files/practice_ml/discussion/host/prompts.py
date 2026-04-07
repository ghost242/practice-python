from __future__ import annotations

"""
Prompt builders for the host agent.

This module defines prompt construction for host-level orchestration decisions.
The host is a controller, not a participant. Its responsibility is to manage
topic progression, subtopic progression, and turn-level speaker selection.

The prompts in this module are designed for structured-output usage. Each
prompt should be paired with a response model from `host.dto`.
"""

from typing import Sequence

from practice_files.practice_ml.discussion.models import (
    Host,
    Participant,
    SubtopicMemory,
    TopicSessionState,
)


# ============================================================================
# Formatting helpers
# ============================================================================


def _safe_text(value: object) -> str:
    """
    Convert an arbitrary value to normalized display text.
    """
    if value is None:
        return ""
    return str(value).strip()


def _format_host(host: Host) -> str:
    """
    Format host identity for prompt context.
    """
    return (
        f"Host ID: {_safe_text(getattr(host, 'participant_id', ''))}\n"
        f"Host Name: {_safe_text(getattr(host, 'display_name', ''))}\n"
        f"Host Role: {_safe_text(getattr(host, 'role', ''))}"
    )


def _format_topic_session(session: TopicSessionState) -> str:
    """
    Format topic session state for prompt context.
    """
    return (
        f"Topic ID: {_safe_text(getattr(session, 'topic_id', ''))}\n"
        f"Topic Title: {_safe_text(getattr(session, 'title', getattr(session, 'topic_title', '')))}\n"
        f"Topic Goal: {_safe_text(getattr(session, 'goal', getattr(session, 'topic_goal', '')))}\n"
        f"Topic Status: {_safe_text(getattr(session, 'status', ''))}\n"
        f"Max Turns: {_safe_text(getattr(session, 'max_turns', ''))}"
    )


def _format_subtopic(subtopic: SubtopicMemory) -> str:
    """
    Format active subtopic state for prompt context.
    """
    return (
        f"Subtopic ID: {_safe_text(getattr(subtopic, 'subtopic_id', ''))}\n"
        f"Subtopic Title: {_safe_text(getattr(subtopic, 'title', ''))}\n"
        f"Description: {_safe_text(getattr(subtopic, 'description', ''))}\n"
        f"Achievement: {_safe_text(getattr(subtopic, 'achievement', ''))}\n"
        f"Status: {_safe_text(getattr(subtopic, 'status', ''))}\n"
        f"Turn Count: {_safe_text(getattr(subtopic, 'turn_count', ''))}\n"
        f"Summary: {_safe_text(getattr(subtopic, 'summary_text', ''))}"
    )


def _format_participant(participant: Participant) -> str:
    """
    Format participant state for prompt context.
    """
    goals = getattr(participant, "goals", None) or []
    traits = getattr(participant, "traits", None) or []
    summary_texts = getattr(participant, "summary_texts", None) or []
    goal_evidence_counts = (
        getattr(participant, "goal_evidence_counts", None) or {}
    )

    return (
        f"Participant ID: {_safe_text(getattr(participant, 'participant_id', getattr(participant, 'actor_id', '')))}\n"
        f"Display Name: {_safe_text(getattr(participant, 'display_name', ''))}\n"
        f"Role: {_safe_text(getattr(participant, 'role', ''))}\n"
        f"Status: {_safe_text(getattr(participant, 'status', getattr(participant, 'participation_status', '')))}\n"
        f"Traits: {', '.join(str(item) for item in traits)}\n"
        f"Goals: {', '.join(str(item) for item in goals)}\n"
        f"Goal Evidence Counts: {goal_evidence_counts}\n"
        f"Latest Summaries: {' | '.join(str(item) for item in summary_texts[-3:])}"
    )


def _format_participants(participants: Sequence[Participant]) -> str:
    """
    Format a participant list for prompt context.
    """
    if not participants:
        return "None"

    blocks: list[str] = []
    for index, participant in enumerate(participants, start=1):
        blocks.append(
            f"[Participant {index}]\n{_format_participant(participant)}"
        )
    return "\n\n".join(blocks)


def _format_recent_turns(subtopic: SubtopicMemory, limit: int = 5) -> str:
    """
    Format recent turns from the subtopic state.

    This function is defensive because the exact turn model may vary.
    """
    turns = getattr(subtopic, "turns", None) or []
    if not turns:
        return "None"

    blocks: list[str] = []
    for turn in list(turns)[-limit:]:
        actor_id = _safe_text(
            getattr(turn, "actor_id", getattr(turn, "participant_id", ""))
        )
        content = _safe_text(
            getattr(turn, "content", getattr(turn, "reply_text", ""))
        )
        turn_index = _safe_text(getattr(turn, "turn_index", ""))
        blocks.append(
            f"Turn {turn_index} | Actor: {actor_id}\n" f"Message: {content}"
        )
    return "\n\n".join(blocks)


# ============================================================================
# System prompts
# ============================================================================


HOST_SYSTEM_PROMPT = """You are the host controller of a structured multi-agent discussion.

Your role is orchestration, not participation.
You do not contribute domain opinions as a speaker.
You must manage discussion flow across topic, subtopic, and turn layers.

Your objectives are:
1. Keep the discussion aligned with the topic goal.
2. Break the topic into useful subtopics when needed.
3. Detect whether a subtopic is making progress or has stalled.
4. Select the best next speaker for the current turn.
5. Close subtopics or the topic when further discussion is unnecessary.

Important rules:
- Focus on control decisions, not content generation.
- Use the provided state only.
- Prefer precise and operational reasoning.
- Avoid vague wording.
- Return structured output that matches the required schema exactly.
"""


# ============================================================================
# Topic prompts
# ============================================================================


def build_define_topic_progress_prompt(
    *,
    host: Host,
    session: TopicSessionState,
) -> tuple[str, str]:
    """
    Build a prompt for defining topic progress as a sequence of subtopics.
    """
    user_prompt = f"""Define a practical ordered subtopic plan for the current topic session.

You must produce subtopics that:
- together cover the topic goal,
- are concrete enough to discuss,
- avoid heavy overlap,
- are suitable for sequential execution.

Return only structured data for TopicProgressDefinitionResult.

[Host]
{_format_host(host)}

[Topic Session]
{_format_topic_session(session)}
"""
    return HOST_SYSTEM_PROMPT, user_prompt


def build_decide_next_subtopic_prompt(
    *,
    host: Host,
    session: TopicSessionState,
) -> tuple[str, str]:
    """
    Build a prompt for deciding the next subtopic or topic closure.
    """
    planned_subtopics = (
        getattr(
            session, "planned_subtopics", getattr(session, "subtopics", [])
        )
        or []
    )
    planned_text = (
        "\n".join(
            [
                (
                    f"- ID: {_safe_text(getattr(item, 'subtopic_id', ''))}, "
                    f"Title: {_safe_text(getattr(item, 'title', ''))}, "
                    f"Status: {_safe_text(getattr(item, 'status', ''))}, "
                    f"Achievement: {_safe_text(getattr(item, 'achievement', ''))}"
                )
                for item in planned_subtopics
            ]
        )
        or "None"
    )

    completed_subtopics = getattr(session, "completed_subtopics", []) or []
    completed_text = (
        "\n".join(str(item) for item in completed_subtopics) or "None"
    )

    user_prompt = f"""Decide whether the topic should continue with another subtopic or close.

Close the topic only if:
- all meaningful subtopics are complete, or
- the topic goal is already sufficiently achieved, or
- further discussion would be redundant.

If the topic should continue, choose the most appropriate next subtopic.

Return only structured data for NextSubtopicDecision.

[Host]
{_format_host(host)}

[Topic Session]
{_format_topic_session(session)}

[Planned Subtopics]
{planned_text}

[Completed Subtopics]
{completed_text}
"""
    return HOST_SYSTEM_PROMPT, user_prompt


# ============================================================================
# Subtopic prompts
# ============================================================================


def build_review_subtopic_progress_prompt(
    *,
    host: Host,
    session: TopicSessionState,
    subtopic: SubtopicMemory,
    participants: Sequence[Participant],
) -> tuple[str, str]:
    """
    Build a prompt for reviewing current subtopic progress.
    """
    user_prompt = f"""Review whether the active subtopic is making meaningful progress.

Evaluate:
- whether recent discussion produced new useful information,
- whether the subtopic achievement appears closer to completion,
- what important points are still missing,
- whether the discussion is drifting or repeating itself.

This is a descriptive assessment, not the final close/continue decision.

Return only structured data for SubtopicProgressReview.

[Host]
{_format_host(host)}

[Topic Session]
{_format_topic_session(session)}

[Active Subtopic]
{_format_subtopic(subtopic)}

[Recent Turns]
{_format_recent_turns(subtopic)}

[Participants]
{_format_participants(participants)}
"""
    return HOST_SYSTEM_PROMPT, user_prompt


def build_subtopic_control_prompt(
    *,
    host: Host,
    session: TopicSessionState,
    subtopic: SubtopicMemory,
    participants: Sequence[Participant],
) -> tuple[str, str]:
    """
    Build a prompt for deciding whether to continue or close the active subtopic.
    """
    user_prompt = f"""Decide whether the active subtopic should continue or close.

Continue when:
- the subtopic still has important unresolved points,
- participants can still add distinct useful contributions,
- the achievement is not yet sufficiently satisfied.

Close when:
- the subtopic achievement has been sufficiently addressed,
- discussion is repetitive,
- no meaningful next contribution is likely.

Return only structured data for SubtopicControlDecision.

[Host]
{_format_host(host)}

[Topic Session]
{_format_topic_session(session)}

[Active Subtopic]
{_format_subtopic(subtopic)}

[Recent Turns]
{_format_recent_turns(subtopic)}

[Participants]
{_format_participants(participants)}
"""
    return HOST_SYSTEM_PROMPT, user_prompt


# ============================================================================
# Turn prompts
# ============================================================================


def build_decide_next_speaker_prompt(
    *,
    host: Host,
    session: TopicSessionState,
    subtopic: SubtopicMemory,
    candidates: Sequence[Participant],
) -> tuple[str, str]:
    """
    Build a prompt for deciding the next speaker.
    """
    user_prompt = f"""Select the next speaker for the current turn.

Choose the participant who is most likely to make the best next contribution
for the active subtopic.

Consider:
- current subtopic achievement,
- recent discussion history,
- participant role and goals,
- whether the participant is likely to add something new,
- whether another participant recently spoke and repetition should be avoided.

If no participant should speak, you may leave `selected_actor_id` empty and
provide a short host message.

Return only structured data for SpeakerDecision.

[Host]
{_format_host(host)}

[Topic Session]
{_format_topic_session(session)}

[Active Subtopic]
{_format_subtopic(subtopic)}

[Recent Turns]
{_format_recent_turns(subtopic)}

[Candidate Participants]
{_format_participants(candidates)}
"""
    return HOST_SYSTEM_PROMPT, user_prompt
