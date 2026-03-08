from __future__ import annotations

import logging
from typing import Sequence, Generator, List
from datetime import datetime, date

from practice_files.practice_ml.conversation_module.types import (
    AgentSpec,
    ConversationState,
    Turn,
)
from practice_files.practice_ml.conversation_module.decision import (
    DecisionAgent,
    decide_for_all_agents,
    choose_speaker,
    decide_session_meta,
    should_finish,
)
from practice_files.practice_ml.conversation_module.generation import (
    generate_reply,
)


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def export_message(
    to_file=False,
    path: str | None = None,
) -> Generator[None, str, None]:
    """
    Optional callback to export each message as it's generated.
    Could be used to stream messages to a UI in real time, for example.
    """
    if path is None:
        path = (
            f"conversation_log.{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        )

    if to_file:
        f = open(path, "a")
    else:
        f = None

    while True:
        text = yield
        if not text:
            break

        print(text)

        if f:
            f.write(text)
            f.flush()


def _init_exporter(export: bool, path: str | None):
    exporter = export_message(to_file=export, path=path)
    next(exporter)
    return exporter


def _close_exporter(exporter):
    if exporter is not None:
        try:
            exporter.close()
        except Exception:
            pass


async def run_multi_agent_chat(
    decider: DecisionAgent,
    agents: List[AgentSpec],
    state: ConversationState,
    *,
    max_turns: int = 50,
    export: bool = False,
    export_path: str | None = None,
):
    """
    Main loop for multi-agent chat.

    Supports:
      - structured-output or JSON-output decisions
      - permanent FINISH removal
      - meta decisions when no agent wants to speak
      - clean exporter close without StopIteration
    """

    # Copy initial agent list, will remove FINISHed agents over time
    active_agents = list(agents)
    turn_idx = 1

    exporter = _init_exporter(export, export_path)

    try:
        while turn_idx <= max_turns and active_agents:
            print(f"\n>> === TURN {turn_idx} ===")

            # 1) Run coordinator decision for all *active* agents
            decisions = await decide_for_all_agents(
                decider, active_agents, state
            )
            print(f"[turn {turn_idx}] decisions: {decisions}")

            # 2) Remove permanently FINISHed agents
            finished_ids = {
                d.agent_id for d in decisions if d.action == "FINISH"
            }
            if finished_ids:
                active_agents = [
                    a for a in active_agents if a.agent_id not in finished_ids
                ]
                if not active_agents:
                    print(">> All agents have finished; ending session.")
                    break

            # 3) Optionally check consensus finish rule
            if should_finish(decisions, state):
                print(">> Consensus finish condition met; closing session.")
                break

            # 4) Choose next speaker
            winner_id = choose_speaker(decisions)
            if winner_id:
                winner = next(
                    a for a in active_agents if a.agent_id == winner_id
                )

                # Generate and export reply
                reply = await generate_reply(winner, state)
                print(f">> Generated reply from {winner_id}:\n{reply}\n")

                # Export locally if requested
                if exporter is not None:
                    exporter.send(
                        f"[{winner_id}:{winner.llm.model_name}] {reply}"
                    )

                # Append turn to conversation
                state.append_turn(winner_id, "agent", reply)
                turn_idx += 1
                continue

            # 5) If no SPEAK candidate (all WAIT), do meta decision
            print(">> No speaker chosen next; invoking meta decision...")
            meta = await decide_session_meta(decider, state)
            print(f">> Meta decision: {meta}")

            if meta.action == "CLOSE":
                print(">> Coordinator decided to close session.")
                break

            # REFRESH: inject subtopic and continue
            if meta.action == "REFRESH":
                refresh_msg = ""
                if meta.subtopic:
                    refresh_msg = (
                        f"Coordinator refresher: focus on '{meta.subtopic}'. "
                        f"{meta.intent}"
                    )
                else:
                    refresh_msg = meta.intent

                print(f">> Injecting REFRESH: {refresh_msg}")

                # Export if needed
                if exporter is not None:
                    exporter.send(f"[coordinator] {refresh_msg}")

                # Append coordinator message and retry next turn
                state.append_turn("coordinator", "system", refresh_msg)
                turn_idx += 1
                continue

            # Safety stop control (should not fall through)
            print(">> Unhandled continuation condition; closing session.")
            break

    finally:
        # Clean up exporter generator without StopIteration
        _close_exporter(exporter)
