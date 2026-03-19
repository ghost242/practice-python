from __future__ import annotations

import os

from langchain.chat_models import BaseChatModel
from langchain_openai import ChatOpenAI

from practice_files.practice_ml.conversation_module.runner import (
    run_multi_agent_chat_sync,
)
from practice_files.practice_ml.conversation_module.types import AgentSpec


def build_chat_model(
    *,
    model: str,
    temperature: float,
) -> BaseChatModel:
    return ChatOpenAI(
        model=model,
        temperature=temperature,
        api_key=os.getenv("OPENAI_API_KEY", ""),
    )


def build_agents(
    *,
    reply_model: str,
    summary_model: str,
    agent_max_turns: int,
) -> list[AgentSpec]:
    olivia = AgentSpec(
        participant_id="olivia",
        display_name="Olivia",
        role="Product Manager",
        traits=[
            "drives the discussion toward a realistic MVP",
            "clarifies service scope and release boundaries",
            "focuses on user value and business feasibility",
            "pushes concrete acceptance criteria",
        ],
        base_knowledge=[
            "product planning for digital content rental platforms",
            "MVP definition for online reading services",
            "browser-based reading flows for rented digital books",
            "time-limited access policy and service scope control",
        ],
        goal=[
            "define a realistic MVP scope for the browser-based EPUB rental service",
            "align the team on core user journeys such as browse, rent, read, expire, and re-rent",
            "prevent scope expansion beyond the first usable release",
        ],
        reply_llm=build_chat_model(
            model=reply_model,
            temperature=0.5,
        ),
        summary_llm=build_chat_model(
            model=summary_model,
            temperature=0.2,
        ),
        max_history_turns=agent_max_turns,
    )

    # ethan = AgentSpec(
    #     participant_id="ethan",
    #     display_name="Ethan",
    #     role="Backend Python Engineer",
    #     traits=[
    #         "focuses on domain correctness and lifecycle rules",
    #         "defines clear service boundaries",
    #         "cares about authorization and entitlement logic",
    #         "avoids premature microservice fragmentation",
    #     ],
    #     base_knowledge=[
    #         "backend domain model for users, books, rentals, entitlements, and access tokens",
    #         "server-side enforcement of rental start time, expiration time, and access revocation",
    #         "API design for catalog, checkout, bookshelf, and reader-open authorization",
    #         "integration patterns between application backend, payment, and DRM provider",
    #     ],
    #     goal=[
    #         "define the minimum backend services and APIs for the EPUB rental platform",
    #         "ensure rental and entitlement rules are enforced on the server side",
    #         "keep the backend architecture maintainable and coherent for the first release",
    #     ],
    #     reply_llm=build_chat_model(
    #         model=reply_model,
    #         temperature=0.2,
    #     ),
    #     summary_llm=build_chat_model(
    #         model=summary_model,
    #         temperature=0.15,
    #     ),
    #     max_history_turns=agent_max_turns,
    # )

    # liam = AgentSpec(
    #     participant_id="liam",
    #     display_name="Liam",
    #     role="Frontend Web Engineer",
    #     traits=[
    #         "focuses on browser-only client behavior",
    #         "cares about stable web-reader integration",
    #         "pushes predictable API contracts and client state handling",
    #         "avoids unnecessary frontend complexity",
    #     ],
    #     base_knowledge=[
    #         "web application flows for storefront, bookshelf, and in-browser EPUB reader",
    #         "client-side handling of authorization, loading, expired rental, and access-denied states",
    #         "browser constraints for protected EPUB rendering and session handling",
    #         "frontend integration patterns for secure reading initiation from backend authorization",
    #     ],
    #     goal=[
    #         "define the frontend structure for catalog, bookshelf, checkout, and reading flow",
    #         "identify the minimum browser-side states needed for DRM-protected reading access",
    #         "keep the browser reading experience robust under loading, authorization, and expiration errors",
    #     ],
    #     reply_llm=build_chat_model(
    #         model=reply_model,
    #         temperature=0.4,
    #     ),
    #     summary_llm=build_chat_model(
    #         model=summary_model,
    #         temperature=0.2,
    #     ),
    #     max_history_turns=agent_max_turns,
    # )

    sophia = AgentSpec(
        participant_id="sophia",
        display_name="Sophia",
        role="UI/UX Designer",
        traits=[
            "optimizes for clarity and trust in the reading flow",
            "translates DRM and rental constraints into understandable UI behavior",
            "reduces confusion around expiration and access states",
            "cares about calm and readable user experience",
        ],
        base_knowledge=[
            "user journeys from discovering a book to renting, opening, reading, and losing access",
            "interaction design for showing remaining rental time and entitlement status",
            "bookshelf organization across active, expired, and previously rented books",
            "messaging patterns for authorization failure, expiration, and blocked actions",
        ],
        goal=[
            "make rental rules and reading permissions understandable to users",
            "reduce friction across storefront, bookshelf, checkout, and reader entry",
            "design failure and expiration states that preserve user trust",
        ],
        reply_llm=build_chat_model(
            model=reply_model,
            temperature=0.6,
        ),
        summary_llm=build_chat_model(
            model=summary_model,
            temperature=0.25,
        ),
        max_history_turns=agent_max_turns,
    )

    john = AgentSpec(
        participant_id="john",
        display_name="John",
        role="System Architect",
        traits=[
            "focuses on end-to-end system structure and service boundaries",
            "cares about simplicity, scalability, and technical coherence",
            "pushes clear integration contracts across frontend, backend, and infrastructure",
            "avoids premature overengineering and fragmented architecture",
        ],
        base_knowledge=[
            "system architecture for browser-based digital content platforms",
            "service decomposition across catalog, checkout, entitlement, reader authorization, and delivery",
            "integration patterns between web application, backend API, payment provider, DRM vendor, CDN, and storage",
            "trade-offs among monolith, modular monolith, and distributed service designs for MVP delivery",
        ],
        goal=[
            "define the minimum viable system architecture for the browser-based EPUB rental service",
            "clarify component boundaries and interactions across client, API, edge, storage, and DRM integration",
            "keep the architecture maintainable, secure, and scalable without unnecessary complexity in the first release",
        ],
        reply_llm=build_chat_model(
            model=reply_model,
            temperature=0.4,
        ),
        summary_llm=build_chat_model(
            model=summary_model,
            temperature=0.2,
        ),
        max_history_turns=agent_max_turns,
    )

    # noah = AgentSpec(
    #     participant_id="noah",
    #     display_name="Noah",
    #     role="DevOps Engineer",
    #     traits=[
    #         "focuses on reliability, operability, and safe deployment",
    #         "highlights risks from external dependencies early",
    #         "cares about observability and rollback paths",
    #         "prefers simple and supportable production topology",
    #     ],
    #     base_knowledge=[
    #         "deployment topology for web frontend, backend API, database, object storage, CDN, and DRM integration",
    #         "secure delivery concerns for protected EPUB assets and short-lived reader authorization",
    #         "observability for checkout failure, reader-open failure, DRM latency, and expiration jobs",
    #         "incident handling and launch readiness for browser-based digital content services",
    #     ],
    #     goal=[
    #         "define a deployment shape that is secure and operable in production",
    #         "identify launch-critical monitoring, alerting, and reliability controls",
    #         "reduce operational fragility in the first release of the service",
    #     ],
    #     reply_llm=build_chat_model(
    #         model=reply_model,
    #         temperature=0.25,
    #     ),
    #     summary_llm=build_chat_model(
    #         model=summary_model,
    #         temperature=0.15,
    #     ),
    #     max_history_turns=agent_max_turns,
    # )

    # mason = AgentSpec(
    #     participant_id="mason",
    #     display_name="Mason",
    #     role="QA / Test Engineer",
    #     traits=[
    #         "focuses on cross-component correctness",
    #         "thinks in integration scenarios and failure cases",
    #         "protects service requirements from accidental regression",
    #         "pushes testability and reproducibility",
    #     ],
    #     base_knowledge=[
    #         "integration testing for catalog, rental, entitlement, and browser reader access flows",
    #         "test scenarios for expiration, authorization denial, retry behavior, and state synchronization",
    #         "validation of service behavior without changing product requirements",
    #         "regression prevention across backend, frontend, and infrastructure boundaries",
    #     ],
    #     goal=[
    #         "define integration test scenarios for the EPUB rental platform",
    #         "identify cross-service failure modes and validation points",
    #         "ensure bug fixes preserve the original service requirements and expected user behavior",
    #     ],
    #     reply_llm=build_chat_model(
    #         model=reply_model,
    #         temperature=0.25,
    #     ),
    #     summary_llm=build_chat_model(
    #         model=summary_model,
    #         temperature=0.15,
    #     ),
    #     max_history_turns=agent_max_turns,
    # )

    return [
        olivia,
        # ethan,
        # liam,
        sophia,
        john,
        # noah,
        # mason,
    ]


def main() -> None:
    if not os.environ.get("OPENAI_API_KEY"):
        raise RuntimeError(
            "OPENAI_API_KEY is not set. Export your OpenAI API key before running."
        )

    decider_model = "gpt-5-mini"
    reply_model = "gpt-5"
    summary_model = "gpt-5-mini"
    agent_max_turns = 20

    decider_llm = build_chat_model(
        model=decider_model,
        temperature=0.1,
    )

    participants = build_agents(
        reply_model=reply_model,
        summary_model=summary_model,
        agent_max_turns=agent_max_turns,
    )

    topic = (
        "Analyze requirements for a web-based DRM-protected EPUB rental service where "
        "users browse, rent, and read books directly in a browser using a web reader. "
        "The system must support time-limited rental access and run entirely in a "
        "standard web browser on the client side without native apps."
    )

    achievement = (
        "Phase 1 requirement analysis.\n"
        "- Identify core user scenarios.\n"
        "- Define non-functional requirements such as scale, reliability, and latency.\n"
        "- Determine technical constraints from browser-only delivery and DRM.\n"
        "- Identify the team roles and responsibilities needed for delivery.\n"
        "- Produce a consolidated synthesis of the discussion before closing."
    )

    state = run_multi_agent_chat_sync(
        topic=topic,
        achievement=achievement,
        participants=participants,
        max_turns_per_subtopic=16,
        host_llm=decider_llm,
        export_path="discussion_log.json",
    )

    print("\n=== FINAL TURNS ===")
    for turn in state.turns:
        print(
            f"[{turn.turn_index}] {turn.speaker_id}/{turn.speaker_type}: {turn.content}"
        )

    print("\n=== FINAL PARTICIPANT STATES ===")
    for participant_id, runtime in state.participant_states.items():
        print(
            f"{participant_id}: "
            f"status={runtime.status}, "
            f"times_spoken={runtime.times_spoken}, "
            f"last_spoken_turn_index={runtime.last_spoken_turn_index}, "
            f"summaries={len(runtime.summary_texts)}"
        )

    print("\n=== SNAPSHOT COUNT ===")
    print(len(state.turn_snapshots))


if __name__ == "__main__":
    main()
