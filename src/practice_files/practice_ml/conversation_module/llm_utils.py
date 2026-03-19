from __future__ import annotations

import json
from typing import Any, Dict


def safe_load_json(text: str) -> Dict[str, Any]:
    text = (text or "").strip()
    if not text:
        return {}

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    start = text.find("{")
    end = text.rfind("}")

    if start != -1 and end != -1 and start < end:
        try:
            return json.loads(text[start : end + 1])
        except json.JSONDecodeError:
            return {}

    return {}


def extract_llm_payload(result: Any) -> Dict[str, Any]:
    if isinstance(result, dict):

        if isinstance(result.get("structured_response"), dict):
            return result["structured_response"]

        content = result.get("content")

        if isinstance(content, dict):
            return content

        if isinstance(content, str):
            parsed = safe_load_json(content)
            if parsed:
                return parsed

        return result

    structured = getattr(result, "structured_response", None)
    if isinstance(structured, dict):
        return structured

    content = getattr(result, "content", None)

    if isinstance(content, dict):
        return content

    if isinstance(content, str):
        parsed = safe_load_json(content)
        if parsed:
            return parsed

    return safe_load_json(str(result))
