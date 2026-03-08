from __future__ import annotations

import logging
import json
import re
from dataclasses import dataclass
from typing import List, Sequence, Optional, Any

from practice_files.practice_ml.conversation_module.types import (
    AgentSpec,
    ConversationState,
    Decision,
    MetaDecision,
    MetaAction,
)
from practice_files.practice_ml.conversation_module.prompts import (
    build_decision_messages,
    build_meta_messages,
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


@dataclass(frozen=True)
class DecisionAgent:
    """
    Dedicated agent for *orchestration decisions*.

    This is intentionally separate from the discussion participants
    (AgentSpec). It owns the LLM used to decide SPEAK / WAIT / FINISH.

    Typical usage:
        decider = DecisionAgent(llm=some_small_model)

    The `llm` may be:
      - a plain chat model that returns text, OR
      - a model wrapped with structured output, returning a dict.
    """

    llm: Any  # must support async ainvoke(messages)


def _safe_load_json(raw: str) -> dict:
    """
    Attempt to robustly parse a JSON object from a model response.

    Small models sometimes wrap JSON in extra text; this function:
    - Tries json.loads(raw) first.
    - If that fails, searches for the first {...} block and retries.
    - Returns {} on failure.
    """
    raw = (raw or "").strip()
    if not raw:
        return {}
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", raw, re.DOTALL)
        if not m:
            return {}
        try:
            return json.loads(m.group(0))
        except json.JSONDecodeError:
            return {}


def _parse_decision_dict(agent_id: str, data: dict) -> Decision:
    """
    Normalize a single agent's decision dict into a Decision object.

    Expected dict fields:
      - action: "SPEAK" | "WAIT" | "FINISH"
      - score:  float 0.0..1.0
      - intent: short string
    """
    print(">> Raw decision JSON from agent %s: %s" % (agent_id, str(data)))

    # Action
    action = str(data.get("action", "WAIT")).upper()
    if action not in ("SPEAK", "WAIT", "FINISH"):
        action = "WAIT"

    # Score
    try:
        score = float(data.get("score", 0.0))
    except Exception as e:
        print(f"Failed to parse score from decision JSON: {e}")
        score = 0.0
    score = max(0.0, min(1.0, score))

    # Intent
    intent = str(data.get("intent", "")).strip()[:64] or "none"

    # If WAIT, score should not influence speaker choice
    if action == "WAIT":
        score = 0.0

    return Decision(
        agent_id=agent_id,
        action=action,
        score=score,
        intent=intent,
    )


async def _raw_decision_call(
    decider: DecisionAgent,
    agents: Sequence[AgentSpec],
    state: ConversationState,
) -> dict:
    """
    Call the decision LLM, supporting:
      - LLM with structured output (returns dict)
      - Plain text result (JSON string inside content)
    """
    messages = build_decision_messages(agents, state)

    # Invoke the model
    result = await decider.llm.ainvoke(messages)

    # Case 1: Model returned a dict directly (structured output)
    if isinstance(result, dict):
        # Result may already be the final JSON object
        if "decisions" in result:
            return result
        # LangChain sometimes wraps structured response in `structured_response`
        if "structured_response" in result and isinstance(
            result["structured_response"], dict
        ):
            return result["structured_response"]
        # If the model wrapped content under "content" as dict, use that
        content = result.get("content", None)
        if isinstance(content, dict) and "decisions" in content:
            return content

        # If no top-level field, assume the whole dict is JSON-like
        return result

    # Case 2: Model returned an object with `.structured_response` (LangChain)
    if hasattr(result, "structured_response"):
        structured = result.structured_response
        if isinstance(structured, dict):
            return structured

    # Case 3: Otherwise, parse raw text from `.content`
    text = getattr(result, "content", None) or str(result)
    return _safe_load_json(text)


async def decide_for_all_agents(
    decider: DecisionAgent,
    agents: Sequence[AgentSpec],
    state: ConversationState,
) -> List[Decision]:
    """
    Run decision calls for all agents and collect their decisions.
    Single coordinator call that returns a decision for each agent.

    If the LLM is configured with structured output, the raw result is
    a dict and is used directly. Otherwise, the result is parsed from
    a JSON string (possibly with surrounding text).
    """
    print(">> Deciding for all agents: %s" % [a.agent_id for a in agents])

    data = await _raw_decision_call(decider, agents, state)
    items = data.get("decisions", [])

    # Index decisions by agent_id for easy lookup
    by_id = {}
    if isinstance(items, list):
        for item in items:
            if not isinstance(item, dict):
                continue
            aid = str(item.get("agent_id", "")).strip()
            if not aid:
                continue
            by_id[aid] = item

    decisions: List[Decision] = []
    for a in agents:
        d_data = by_id.get(a.agent_id, {})
        decision = _parse_decision_dict(a.agent_id, d_data)
        decisions.append(decision)

    return decisions


def choose_speaker(
    decisions: Sequence[Decision],
    *,
    min_floor: float = 0.15,
    min_margin: float = 0.03,
) -> Optional[str]:
    """
    Pick one agent_id to SPEAK based on scores, or None.

    Logic:
    - Filter to decisions with action == "SPEAK".
    - Sort by score descending.
    - Reject if top score < min_floor.
    - (min_margin currently not enforced; only floor is used.)

    The continuation semantics (e.g., same agent speaking twice)
    are expressed in the decision prompt, which sets the scores.
    """
    print(">> Choosing speaker from decisions: %s" % decisions)

    speak = [d for d in decisions if d.action == "SPEAK"]
    if not speak:
        # No one wants to speak this turn
        return None

    speak_sorted = sorted(speak, key=lambda d: d.score, reverse=True)
    top1 = speak_sorted[0]

    if top1.score < min_floor:
        print(
            ">> No speaker chosen: top score %.2f below floor %.2f"
            % (top1.score, min_floor)
        )
        return None

    return top1.agent_id


def should_finish(
    decisions: Sequence[Decision],
    state: ConversationState,
    *,
    min_turns: int = 4,
    min_votes: int = 2,
    min_score: float = 0.7,
) -> bool:
    """
    Decide whether the discussion should finish.

    Guards (aligned with the global FSM):
      - Do NOT allow finish while the discussion is very short
        (len(state.turns) < min_turns).
      - Require at least `min_votes` agents choosing FINISH
        with score >= min_score.
    """
    n_turns = len(state.turns)
    if n_turns < min_turns:
        print(
            ">> should_finish: too early to finish (turns=%d < min_turns=%d)"
            % (n_turns, min_turns)
        )
        return False

    votes = [
        d for d in decisions if d.action == "FINISH" and d.score >= min_score
    ]
    print(
        ">> should_finish: %d FINISH votes with score >= %.2f (min_votes=%d)"
        % (len(votes), min_score, min_votes)
    )
    return len(votes) >= min_votes


def _normalize_meta_action(raw_action: Any) -> MetaAction:
    """
    Normalize meta action to one of: 'REFRESH', 'CLOSE'.
    Default to 'CLOSE' on unknown values.
    """
    action = str(raw_action or "").upper()
    if action not in ("REFRESH", "CLOSE"):
        action = "CLOSE"
    return action


async def decide_session_meta(
    decider: DecisionAgent,
    state: ConversationState,
) -> MetaDecision:
    """
    Called when no agent wants to SPEAK (all WAIT / FINISH).
    The decision agent decides whether to:
      - REFRESH: propose a new subtopic / angle to advance the Goal.
      - CLOSE: end the discussion as unnecessary to continue.

    Supports both structured-output dicts and plain-text JSON.
    """
    messages = build_meta_messages(state)
    _structured_model = decider.llm.with_structured_output(MetaDecision)
    result = await _structured_model.ainvoke(messages)

    # Structured-output dict case
    if isinstance(result, dict):
        # If it already looks like the meta JSON, use directly.
        if any(k in result for k in ("action", "subtopic", "intent")):
            data = result
        else:
            content = result.get("content", "")
            data = _safe_load_json(content)
    else:
        # Message-style or other object
        content = getattr(result, "content", None)
        if isinstance(content, dict):
            if any(k in content for k in ("action", "subtopic", "intent")):
                data = content
            else:
                data = _safe_load_json(json.dumps(content))
        elif isinstance(content, str):
            data = _safe_load_json(content)
        else:
            data = _safe_load_json(str(result))

    action = _normalize_meta_action(data.get("action", "CLOSE"))
    subtopic = str(data.get("subtopic", "") or "")
    intent = str(data.get("intent", "") or "")

    return MetaDecision(
        action=action,
        subtopic=subtopic,
        intent=intent,
    )
