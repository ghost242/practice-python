from __future__ import annotations

from types import SimpleNamespace

from langchain_ollama import ChatOllama

from practice_files.practice_ml.conversation_module.runner import (
    run_multi_agent_chat_sync,
)
from practice_files.practice_ml.conversation_module.types import AgentSpec


def build_agents(
    base_url: str,
    model_names: list[str],
    agent_max_turns: int,
) -> tuple[list[AgentSpec], object]:
    """
    Build discussion agents and a lightweight decider wrapper.

    Notes:
    - The runner requires `decider.llm.ainvoke(...)`.
    - `model_names[0]` is used for speaking replies.
    - `model_names[1]` is used for summary/evaluation.
    - `model_names[2]` is used for the coordinator / decider.
    """
    olivia = AgentSpec(
        participant_id="olivia",
        display_name="Olivia",
        role="Product Manager",
        traits=[
            "drives the discussion toward a shippable MVP",
            "prioritizes user value and release scope",
            "reduces ambiguity in service definition",
            "pushes concrete acceptance criteria",
        ],
        base_knowledge=[
            "launching an EPUB rental service with a limited initial catalog",
            "defining first-release user flows for browse, rent, read, expire, and re-rent",
            "business constraints around time-limited access to rented digital books",
            "scoping what must exist before a public MVP launch versus later phases",
        ],
        goal=[
            "define a realistic MVP scope for the DRM-protected EPUB rental service",
            "align the team on essential user flows and operational boundaries",
            "produce a phased release plan instead of an overbuilt first version",
        ],
        reply_llm=ChatOllama(
            model=model_names[0],
            base_url=base_url,
            temperature=0.5,
        ),
        summary_llm=ChatOllama(
            model=model_names[1],
            base_url=base_url,
            temperature=0.2,
        ),
        max_history_turns=agent_max_turns,
    )

    liam = AgentSpec(
        participant_id="liam",
        display_name="Liam",
        role="Frontend React Engineer",
        traits=[
            "focuses on stable client behavior and explicit UI states",
            "cares about reader initialization and failure recovery",
            "pushes predictable API contracts",
            "avoids unnecessary frontend complexity",
        ],
        base_knowledge=[
            "React screens for storefront, bookshelf, and browser-based EPUB reader",
            "UI states for rental activation, reader loading, expired access, and authorization failure",
            "client integration patterns for fetching reader authorization before opening a title",
            "handling large-book loading and retry behavior in a web reader",
        ],
        goal=[
            "define the frontend structure for bookstore, bookshelf, and reading flow",
            "identify the minimum client-side states needed for DRM-protected book access",
            "keep the MVP reading experience robust under loading and access errors",
        ],
        reply_llm=ChatOllama(
            model=model_names[0],
            base_url=base_url,
            temperature=0.4,
        ),
        summary_llm=ChatOllama(
            model=model_names[1],
            base_url=base_url,
            temperature=0.2,
        ),
        max_history_turns=agent_max_turns,
    )

    ethan = AgentSpec(
        participant_id="ethan",
        display_name="Ethan",
        role="Backend Python Engineer",
        traits=[
            "focuses on correctness and explicit lifecycle rules",
            "separates domain logic from infrastructure concerns",
            "prefers clear service boundaries",
            "questions vague assumptions about access control",
        ],
        base_knowledge=[
            "backend domain model for users, titles, rentals, entitlements, and reader authorization",
            "server-side enforcement of rental start time, expiration time, and access revocation",
            "API boundaries for catalog, checkout, bookshelf, and reader-open authorization",
            "integration points between application backend, payment flow, and external DRM service",
        ],
        goal=[
            "define the minimum backend services and APIs for the rental platform",
            "ensure rental and entitlement rules are enforced server-side",
            "make the MVP architecture maintainable without premature service fragmentation",
        ],
        reply_llm=ChatOllama(
            model=model_names[0],
            base_url=base_url,
            temperature=0.2,
        ),
        summary_llm=ChatOllama(
            model=model_names[1],
            base_url=base_url,
            temperature=0.15,
        ),
        max_history_turns=agent_max_turns,
    )

    sophia = AgentSpec(
        participant_id="sophia",
        display_name="Sophia",
        role="UI/UX Designer",
        traits=[
            "optimizes for user clarity and trust",
            "translates constraints into understandable UI behavior",
            "reduces confusion around entitlement and expiration",
            "cares about readable and calm reading flow",
        ],
        base_knowledge=[
            "user journey from discovering a book to renting, opening, reading, and losing access",
            "interaction design for showing remaining rental time and access status",
            "bookshelf organization across active rentals, expired rentals, and owned books",
            "messaging patterns for authorization failure, expired rentals, and restricted actions",
        ],
        goal=[
            "make rental rules understandable without requiring technical explanation",
            "reduce friction between storefront, bookshelf, and reader entry",
            "design failure and expiration states that preserve user trust",
        ],
        reply_llm=ChatOllama(
            model=model_names[0],
            base_url=base_url,
            temperature=0.6,
        ),
        summary_llm=ChatOllama(
            model=model_names[1],
            base_url=base_url,
            temperature=0.25,
        ),
        max_history_turns=agent_max_turns,
    )

    noah = AgentSpec(
        participant_id="noah",
        display_name="Noah",
        role="DevOps Engineer",
        traits=[
            "focuses on reliability, traceability, and safe deployment",
            "highlights external dependency risks early",
            "cares about observability and rollback paths",
            "prefers operational simplicity for the first release",
        ],
        base_knowledge=[
            "deployment topology for web app, backend API, database, object storage, and DRM integration",
            "secure delivery considerations for protected EPUB assets and short-lived authorization paths",
            "observability for checkout failure, reader authorization failure, and DRM-service latency",
            "operational concerns around expiration jobs, retry handling, and launch-time incident response",
        ],
        goal=[
            "define an MVP deployment shape that is secure and operable",
            "identify launch-critical observability and reliability controls",
            "prevent the first release from depending on brittle manual operations",
        ],
        reply_llm=ChatOllama(
            model=model_names[0],
            base_url=base_url,
            temperature=0.25,
        ),
        summary_llm=ChatOllama(
            model=model_names[1],
            base_url=base_url,
            temperature=0.15,
        ),
        max_history_turns=agent_max_turns,
    )

    agents = [olivia, liam, ethan, sophia, noah]

    decider = SimpleNamespace(
        llm=ChatOllama(
            model=model_names[0],
            base_url=base_url,
            temperature=0.1,
        )
    )

    return agents, decider


def main() -> None:
    base_url = "http://ollama:11434"
    # model_names = [
    #     "gpt-oss:20b",   # reply model
    #     "phi4:14b",      # summary/evaluation model
    #     "llama3.2:3b",   # decider model
    # ]
    model_names = [
        "phi4:14b",  # reply model
        "phi4:14b",  # summary/evaluation model
        "llama3.2:3b",  # decider model
    ]
    agent_max_turns = 20

    agents, decider = build_agents(
        base_url=base_url,
        model_names=model_names,
        agent_max_turns=agent_max_turns,
    )

    topic = (
        "Design an online digital library service that rents DRM-protected EPUB books. "
        "Users should be able to browse the catalog, rent a title for a limited time, "
        "open it in a web reader, and lose access automatically when the rental expires."
    )

    achievement = (
        "Reach a concrete MVP plan covering essential user flows, minimal backend and frontend "
        "architecture, DRM-related access control boundaries, and launch-critical operational risks."
    )

    user_message = (
        "We are starting a product discussion for a DRM-protected EPUB rental platform. "
        "Please identify the minimum viable product scope first. I do not want a full enterprise "
        "platform yet; I want a realistic first release that users can actually use."
    )

    state = run_multi_agent_chat_sync(
        decider=decider,
        participants=agents,
        topic=topic,
        achievement=achievement,
        user_message=user_message,
        max_turns=40,
    )

    print("\n=== FINAL CONVERSATION ===\n")
    for turn in state.turns:
        print(f"[{turn.speaker_type}] {turn.speaker_id}: {turn.content}")


if __name__ == "__main__":
    main()
