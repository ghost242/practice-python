from __future__ import annotations

from typing import Any, Literal, List, Optional

from pydantic import BaseModel, Field, ConfigDict


DecisionAction = Literal["SPEAK", "WAIT", "FINISH"]
MetaAction = Literal["REFRESH", "CLOSE"]


class AgentSpec(BaseModel):
    """
    Static specification for a discussion agent.

    Notes:
    - `llm` is an arbitrary object (LangChain ChatModel, custom wrapper, etc.).
    - `prompt` contains persona/style instructions injected into agent prompts.
    - `max_history_turns` controls how much conversation context the agent sees.
    """

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        frozen=True,  # similar to @dataclass(frozen=True)
    )

    agent_id: str  # e.g. "olivia"
    role: str  # e.g. "Product Manager"
    prompt: str  # persona instructions
    llm: Any  # must support async ainvoke(messages)
    max_history_turns: int = 15


class UserSpec(BaseModel):
    """
    Static specification for the user.

    Could be extended with traits, preferences, etc. in the future.
    """

    model_config = ConfigDict(
        frozen=True,
    )

    user_id: str = "user"
    user_name: str
    role: str
    traits: str


class Turn(BaseModel):
    """
    Single message in the conversation history.
    """

    speaker_id: str  # "user" or agent_id or "coordinator"
    speaker_type: Literal["user", "agent", "system"]
    content: str


class ConversationState(BaseModel):
    """
    Shared conversation state for the whole session.

    - `topic`: high-level subject of discussion.
    - `achievement`: target goal / outcome description.
    - `turns`: chronological list of turns.
    """

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
    )

    topic: str
    achievement: str
    turns: List[Turn] = Field(default_factory=list)

    @property
    def last_turn(self) -> Optional[Turn]:
        return self.turns[-1] if self.turns else None

    def append_turn(
        self,
        speaker_id: str,
        speaker_type: Literal["user", "agent", "system"],
        content: str,
    ) -> None:
        """
        Append a new Turn to the conversation, in-place.
        """
        self.turns.append(
            Turn(
                speaker_id=speaker_id,
                speaker_type=speaker_type,
                content=content,
            )
        )


class Decision(BaseModel):
    """
    Orchestration decision for a single agent.
    """

    model_config = ConfigDict(
        frozen=True,  # value object semantics
    )

    agent_id: str
    action: DecisionAction
    score: float  # 0.0..1.0
    intent: str  # short reason / intent


class MetaDecision(BaseModel):
    """
    Global meta decision when no agent wants to SPEAK.

    - REFRESH: coordinator injects a new subtopic/angle.
    - CLOSE:   end the session.
    """

    model_config = ConfigDict(
        frozen=True,
    )

    action: MetaAction
    subtopic: str  # may be empty when action == "CLOSE"
    intent: str  # brief explanation
