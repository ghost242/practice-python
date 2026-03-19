from __future__ import annotations

from typing import Any, Sequence

from practice_files.practice_ml.conversation_module.llm_utils import (
    extract_llm_payload,
)
from practice_files.practice_ml.conversation_module.prompts import (
    build_agent_summary_update_messages,
    build_final_synthesis_messages,
    build_reply_messages,
)
from practice_files.practice_ml.conversation_module.types import (
    AgentSpec,
    ConversationState,
    ReplyResult,
)


# ---------------------------------------------------------
# helpers
# ---------------------------------------------------------


def _strip_outer_quotes(text: str) -> str:
    text = (text or "").strip()
    if len(text) >= 2 and text[0] == text[-1] and text[0] in {"'", '"'}:
        return text[1:-1].strip()
    return text


def _normalize_string_list(value: Any) -> list[str]:
    if value is None:
        return []

    if isinstance(value, str):
        text = _strip_outer_quotes(value).strip()
        return [text] if text else []

    if isinstance(value, list):
        items: list[str] = []
        for item in value:
            text = _strip_outer_quotes(str(item or "")).strip()
            if text:
                items.append(text)
        return items

    text = _strip_outer_quotes(str(value)).strip()
    return [text] if text else []


# ---------------------------------------------------------
# reply generation
# ---------------------------------------------------------


async def generate_agent_reply(
    agent: AgentSpec,
    state: ConversationState,
) -> ReplyResult:
    messages = build_reply_messages(agent, state)

    print("\n[LLM] generate_agent_reply()")
    print("[LLM] agent:", agent.participant_id)
    print("[LLM] prompt size:", sum(len(m["content"]) for m in messages))

    try:
        result = await agent.reply_llm.ainvoke(messages)
    except Exception as exc:
        print("[LLM] ERROR invoking model:", exc)
        return ReplyResult(reply="Model invocation failed.", intent="error")

    print("[LLM] raw result:", result)

    payload = extract_llm_payload(result)

    print("[LLM] parsed payload:", payload)

    reply = _strip_outer_quotes(str(payload.get("reply", "") or ""))
    intent = _strip_outer_quotes(str(payload.get("intent", "") or ""))

    # fallback if JSON not produced
    if not reply:
        content = getattr(result, "content", None)

        if isinstance(content, str) and content.strip():
            print("[LLM] fallback: using raw text response")
            reply = content.strip()

    if not reply:
        print("[LLM] fallback: empty response")
        reply = "No meaningful response."

    return ReplyResult(
        reply=reply,
        intent=intent,
    )


# ---------------------------------------------------------
# summary extraction
# ---------------------------------------------------------


async def update_agent_summary_from_history(
    agent: AgentSpec,
    state: ConversationState,
) -> str:
    runtime = state.get_participant_state(agent.participant_id)

    messages = build_agent_summary_update_messages(agent, state)

    print("\n[LLM] update_agent_summary_from_history()")
    print("[LLM] agent:", agent.participant_id)
    print("[LLM] prompt size:", sum(len(m["content"]) for m in messages))

    try:
        result = await agent.summary_llm.ainvoke(messages)
    except Exception as exc:
        print("[LLM] ERROR invoking summary model:", exc)
        return "Summary extraction failed."

    print("[LLM] raw result:", result)

    payload = extract_llm_payload(result)

    print("[LLM] parsed payload:", payload)

    summary = _strip_outer_quotes(str(payload.get("summary", "") or ""))
    latest_open_questions = _normalize_string_list(
        payload.get("latest_open_questions")
    )
    current_focus = _strip_outer_quotes(
        str(payload.get("current_focus", "") or "")
    )

    if not summary:
        summary = "No clear progress."

    runtime.summary_text = summary
    runtime.latest_open_questions = list(
        dict.fromkeys(runtime.latest_open_questions + latest_open_questions)
    )

    if current_focus:
        runtime.current_focus = current_focus

    return summary


# ---------------------------------------------------------
# final synthesis
# ---------------------------------------------------------


async def generate_final_synthesis(
    *,
    state: ConversationState,
    participants: Sequence[AgentSpec],
    host_llm: Any | None,
) -> str:
    if host_llm is None:
        return ""

    messages = build_final_synthesis_messages(state, participants)

    print("\n[LLM] generate_final_synthesis()")
    print("[LLM] prompt size:", sum(len(m["content"]) for m in messages))

    try:
        result = await host_llm.ainvoke(messages)
    except Exception as exc:
        print("[LLM] ERROR invoking synthesis model:", exc)
        return ""

    print("[LLM] raw result:", result)

    payload = extract_llm_payload(result)

    print("[LLM] parsed payload:", payload)

    synthesis = _strip_outer_quotes(str(payload.get("synthesis", "") or ""))
    open_items = _normalize_string_list(payload.get("open_items"))
    next_steps = _normalize_string_list(payload.get("next_steps"))

    parts: list[str] = []

    if synthesis:
        parts.append(synthesis)

    if open_items:
        parts.append("Open items: " + "; ".join(open_items))

    if next_steps:
        parts.append("Next steps: " + "; ".join(next_steps))

    return " | ".join(parts).strip()
