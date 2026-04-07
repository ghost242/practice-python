from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


# ============================================================================
# Shared enums
# ============================================================================


class ActorType(str, Enum):
    """
    Type of actor in the discussion system.
    """

    HOST = "HOST"
    PARTICIPANT = "PARTICIPANT"
    USER = "USER"


class ActorStatus(str, Enum):
    """
    General runtime availability of an actor.
    """

    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    BLOCKED = "BLOCKED"
    LEFT = "LEFT"


class ParticipantStatus(str, Enum):
    """
    Participation progress state of a speaking actor in the discussion.
    """

    ONGOING = "ONGOING"
    WAITING = "WAITING"
    FINISHED = "FINISHED"
    INACTIVE = "INACTIVE"


class TopicStatus(str, Enum):
    """
    Lifecycle status of the topic session itself.
    """

    PENDING = "PENDING"
    OPEN = "OPEN"
    RUNNING = "RUNNING"
    CLOSING = "CLOSING"
    CLOSED = "CLOSED"
    FAILED = "FAILED"


class SubtopicStatus(str, Enum):
    """
    Lifecycle status of one subtopic within the topic session.
    """

    PENDING = "PENDING"
    OPEN = "OPEN"
    RUNNING = "RUNNING"
    REVIEWING = "REVIEWING"
    CLOSING = "CLOSING"
    CLOSED = "CLOSED"
    FAILED = "FAILED"


# ============================================================================
# Shared actor models
# ============================================================================


class Actor(BaseModel):
    """
    Minimal identity and availability state shared by all actors.

    This is the common root model for host, participant, and user.
    It intentionally contains only fields that are meaningful for every actor.
    """

    actor_id: str
    actor_type: ActorType
    display_name: str

    description: str = ""
    status: ActorStatus = ActorStatus.ACTIVE


class SpeakingActor(Actor):
    """
    Base model for actors that can produce a message when selected for a turn.

    Participant and user both inherit from this because both can be chosen
    by the host as the next speaker in a turn.
    """

    can_speak: bool = True

    latest_message: str = ""
    latest_turn_index: Optional[int] = None


class Participant(SpeakingActor):
    """
    Mutable runtime state for one LLM-driven participant.

    A participant is a speaking actor that contributes using its role,
    prompt, knowledge, and achievement goals.
    """

    actor_type: ActorType = ActorType.PARTICIPANT

    role: str
    prompt: str = ""

    base_knowledge: list[str] = Field(default_factory=list)
    goals: list[str] = Field(default_factory=list)

    participation_status: ParticipantStatus = ParticipantStatus.ONGOING

    summary_texts: list[str] = Field(default_factory=list)
    goal_evidence_counts: dict[int, int] = Field(default_factory=dict)


class UserParticipant(Participant):
    """
    Mutable runtime state for a human user participating in the discussion.

    The user is modeled as a specialized participant because the user can be
    selected by the host at turn time and contributes through the same turn
    pipeline, even though the message source is external human input instead
    of LLM generation.
    """

    actor_type: ActorType = ActorType.USER

    user_external_id: Optional[str] = None
    is_human_input_required: bool = True


class Host(Actor):
    """
    Mutable runtime state for the host controller.

    The host governs session flow across topic, subtopic, and turn layers.
    It is not modeled as a normal speaking participant.
    """

    actor_type: ActorType = ActorType.HOST

    system_prompt: str = ""
    authority_note: str = ""


# ============================================================================
# Shared leaf/domain models
# ============================================================================


class Turn(BaseModel):
    """
    Result of one turn execution.

    In this system, a turn is the process unit in which the host selects
    one actor and the selected actor produces one message. This model stores
    the committed output of that process.
    """

    turn_index: int = 0

    actor_id: str
    actor_type: ActorType
    actor_name: str = ""

    content: str = ""
    summary_text: str = ""

    subtopic_id: Optional[str] = None


class SubtopicMemory(BaseModel):
    """
    Mutable runtime state for one subtopic session.

    A subtopic session is a focused discussion scope that contains repeated
    turn executions governed by the host.
    """

    subtopic_id: str
    title: str
    description: str = ""
    achievement: str = ""

    status: SubtopicStatus = SubtopicStatus.PENDING
    is_active: bool = False

    turn_count: int = 0
    summary_text: str = ""

    turns: list[Turn] = Field(default_factory=list)


class TopicSessionState(BaseModel):
    """
    Mutable runtime state for the whole topic session.

    Topic progress is defined through subtopics. The topic session therefore
    tracks the set of subtopic sessions and their overall progression.
    """

    topic_id: str
    title: str
    goal: str = ""

    status: TopicStatus = TopicStatus.PENDING

    turn_count: int = 0
    max_turns: int = 0

    opened_subtopic_count: int = 0
    closed_subtopic_count: int = 0

    subtopics: list[SubtopicMemory] = Field(default_factory=list)

    close_reason: str = ""


# ============================================================================
# Shared read-only snapshots
# ============================================================================


class ActorSnapshot(BaseModel):
    """
    Read-only projection of actor identity and availability.
    """

    actor_id: str
    actor_type: ActorType
    display_name: str

    description: str = ""
    status: ActorStatus


class ParticipantSnapshot(ActorSnapshot):
    """
    Read-only participant projection used in orchestration prompts and decisions.
    """

    actor_type: ActorType = ActorType.PARTICIPANT

    role: str
    participation_status: ParticipantStatus

    latest_message: str = ""
    latest_turn_index: Optional[int] = None

    goals: list[str] = Field(default_factory=list)
    summary_texts: list[str] = Field(default_factory=list)


class UserParticipantSnapshot(ParticipantSnapshot):
    """
    Read-only projection of a human user participant.
    """

    actor_type: ActorType = ActorType.USER

    user_external_id: Optional[str] = None


class HostSnapshot(ActorSnapshot):
    """
    Read-only projection of the host controller.
    """

    actor_type: ActorType = ActorType.HOST

    authority_note: str = ""


class SubtopicSnapshot(BaseModel):
    """
    Read-only projection of one subtopic.
    """

    subtopic_id: str
    title: str
    description: str = ""
    achievement: str = ""

    status: SubtopicStatus
    turn_count: int = 0
    summary_text: str = ""


class TopicSnapshot(BaseModel):
    """
    Read-only projection of the current topic session state.
    """

    topic_id: str
    title: str
    goal: str = ""

    status: TopicStatus

    turn_count: int = 0
    max_turns: int = 0

    opened_subtopic_count: int = 0
    closed_subtopic_count: int = 0
