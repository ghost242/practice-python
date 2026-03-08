from __future__ import annotations

import logging
import asyncio
from typing import List, Tuple

from langchain_ollama import ChatOllama

from practice_files.practice_ml.conversation_module.types import (
    AgentSpec,
    ConversationState,
)
from practice_files.practice_ml.conversation_module.decision import (
    DecisionAgent,
)
from practice_files.practice_ml.conversation_module.runner import (
    run_multi_agent_chat,
)


def build_agents(
    base_url: str, model_names: List[str], agent_max_turns: int
) -> Tuple[List[AgentSpec], DecisionAgent]:
    return (
        [
            AgentSpec(
                agent_id="olivia",
                role="Product Manager",
                prompt=(
                    "Strategic, pragmatic, and user-obsessed. \n"
                    "Thinks in terms of business impact, prioritization, and measurable outcomes. \n"
                    "Frequently asks about user segments, KPIs, roadmap alignment, trade-offs, and MVP scope. \n"
                    "Pushes the team to clarify the core problem and success criteria. \n"
                    "Avoids deep technical detail unless it affects delivery timeline, cost, or user value. \n"
                    "Calm but firm in steering discussions back to product goals."
                ),
                llm=ChatOllama(
                    model=model_names[0],
                    base_url=base_url,
                    temperature=0.5,
                ),
                max_history_turns=agent_max_turns,
            ),
            AgentSpec(
                agent_id="liam",
                role="Frontend React Engineer",
                prompt=(
                    "Detail-oriented, performance-conscious, and pragmatic. \n"
                    "Focuses on React architecture, state management, API contracts, and UI responsiveness. \n"
                    "Asks about latency impact on rendering, error states, loading transitions, and data shape. \n"
                    "Prefers clear interfaces and predictable backend behavior. \n"
                    "Occasionally impatient with vague API definitions."
                ),
                llm=ChatOllama(
                    model=model_names[0],
                    base_url=base_url,
                    temperature=0.4,
                ),
                max_history_turns=agent_max_turns,
            ),
            AgentSpec(
                agent_id="ethan",
                role="Backend Python Engineer",
                prompt=(
                    "Analytical, structured, and correctness-driven. \n"
                    "Focuses on API design, data modeling, concurrency control, async patterns, \n"
                    "transaction boundaries, and schema validation. \n"
                    "Concerned with maintainability, clarity, and data integrity. \n"
                    "Prefers explicit invariants and well-defined contracts. \n"
                    "Skeptical of overly complex distributed patterns without clear necessity."
                ),
                llm=ChatOllama(
                    model=model_names[0],
                    base_url=base_url,
                    temperature=0.2,
                ),
                max_history_turns=agent_max_turns,
            ),
            AgentSpec(
                agent_id="sophia",
                role="UI/UX Designer",
                prompt=(
                    "Empathetic, user-centered, and clarity-focused. \n"
                    "Thinks in user journeys, mental models, and cognitive load. \n"
                    "Questions how system states (loading, stale data, rollback, errors) are presented to users. \n"
                    "Advocates for simplicity, visual hierarchy, and accessibility. \n"
                    "Often reframes technical discussions into human-centered impact."
                ),
                llm=ChatOllama(
                    model=model_names[0],
                    base_url=base_url,
                    temperature=0.6,
                ),
                max_history_turns=agent_max_turns,
            ),
            AgentSpec(
                agent_id="noah",
                role="DevOps Engineer",
                prompt=(
                    "Reliability-focused, automation-driven, and risk-aware. \n"
                    "Thinks in CI/CD pipelines, container orchestration, infrastructure as code, \n"
                    "observability, rollback automation, and resource limits. \n"
                    "Asks about deployment reproducibility, environment isolation, scaling limits, and operational cost. \n"
                    "Prefers deterministic processes and minimal manual intervention."
                ),
                llm=ChatOllama(
                    model=model_names[0],
                    base_url=base_url,
                    temperature=0.25,
                ),
                max_history_turns=agent_max_turns,
            ),
        ],
        DecisionAgent(
            llm=ChatOllama(
                model=model_names[2],
                base_url=base_url,
                temperature=0.1,
            )
        ),
    )


async def main():
    topic = (
        "Design a service architecture and development plan for an EPUB-based "
        "digital library that executes DRM-protected books and supports a rental model."
    )
    achievement = (
        "Goal: agree on architecture, key requirements, MVP phases, and a basic "
        "business model for EPUB+DRM rental."
    )

    state = ConversationState(topic=topic, achievement=achievement)

    kickoff = (
        "We’re designing an EPUB-based digital library service that executes "
        "DRM-protected books and supports a time-limited rental model. "
        "Please discuss architecture, key requirements, MVP plan, "
        "and a simple rental vs purchase business model."
    )
    state.append_turn("user", "user", kickoff)

    base_url = "http://ollama:11434"
    model_names = [
        "gpt-oss:20b",
        "phi4:latest",
        "llama3.2:3b",
    ]

    agents, decider = build_agents(
        base_url,
        model_names,
        agent_max_turns=30,
    )

    await run_multi_agent_chat(
        decider, agents, state, max_turns=40, export=True
    )


if __name__ == "__main__":
    logging.getLogger().setLevel(logging.DEBUG)
    asyncio.run(main())
