from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Sequence

from practice_files.practice_ml.conversation_module.types import (
    ConversationState,
    DiscussionParticipant,
    ParticipantRuntimeState,
    SubtopicPlan,
    Turn,
    TurnSnapshot,
)


def _runtime_payload(runtime: ParticipantRuntimeState) -> dict:
    return {
        "times_spoken": runtime.times_spoken,
        "last_spoken_turn_index": runtime.last_spoken_turn_index,
        "latest_reply": runtime.latest_reply,
        "status": runtime.status,
        "summary_text": runtime.summary_text,
        "latest_open_questions": list(runtime.latest_open_questions),
        "current_focus": runtime.current_focus,
    }


def _participant_payload(participant: DiscussionParticipant) -> dict:
    payload = {
        "participant_id": participant.participant_id,
        "display_name": participant.display_name,
        "role": participant.role,
        "kind": participant.kind,
        "traits": list(participant.traits),
        "goal": list(participant.goal),
        "base_knowledge": list(participant.base_knowledge),
        "can_self_generate": participant.can_self_generate,
    }

    if hasattr(participant, "max_history_turns"):
        payload["max_history_turns"] = getattr(
            participant,
            "max_history_turns",
            None,
        )

    return payload


def _subtopic_payload(subtopic: SubtopicPlan) -> dict:
    return {
        "subtopic_id": subtopic.subtopic_id,
        "title": subtopic.title,
        "kickoff_message": subtopic.kickoff_message,
        "achievement": subtopic.achievement,
        "conclusion": subtopic.conclusion,
        "status": subtopic.status,
    }


def _turn_payload(turn: Turn) -> dict:
    return {
        "turn_index": turn.turn_index,
        "participant_id": turn.participant_id,
        "participant_type": turn.participant_type,
        "content": turn.content,
    }


def _snapshot_payload(snapshot: TurnSnapshot) -> dict:
    return {
        "turn_index": snapshot.turn_index,
        "participant_id": snapshot.participant_id,
        "participant_type": snapshot.participant_type,
        "content": snapshot.content,
        "latest_message_index": snapshot.latest_message_index,
        "summary": snapshot.summary,
        "latest_open_questions": list(snapshot.latest_open_questions),
    }


def export_discussion(
    state: ConversationState,
    participants: Sequence[DiscussionParticipant],
    path: str,
) -> Path:
    export_data = {
        "topic": state.topic,
        "achievement": state.achievement,
        "current_subtopic_index": state.current_subtopic_index,
        "subtopics": [
            _subtopic_payload(subtopic) for subtopic in state.subtopics
        ],
        "participants": [
            _participant_payload(participant) for participant in participants
        ],
        "turns": [_turn_payload(turn) for turn in state.turns],
        "participant_states": {
            participant_id: _runtime_payload(runtime)
            for participant_id, runtime in state.participant_states.items()
        },
        "turn_snapshots": [
            _snapshot_payload(snapshot) for snapshot in state.turn_snapshots
        ],
    }

    timestamp_dir = Path("artifacts") / str(int(time.time()))
    timestamp_dir.mkdir(parents=True, exist_ok=True)

    output_path = timestamp_dir / Path(path).name
    output_path.write_text(
        json.dumps(export_data, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    return output_path
