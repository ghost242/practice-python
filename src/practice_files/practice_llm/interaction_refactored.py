from __future__ import annotations

from dataclasses import dataclass, field, fields
from typing import Callable, Iterable, List, Optional
import logging
from logging.handlers import RotatingFileHandler
import time

import chromadb
from langchain_chroma import Chroma
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    SystemMessage,
)
from langchain_ollama import ChatOllama, OllamaEmbeddings

logger = logging.getLogger(__name__)


def configure_file_logging(
    *,
    log_path: str = "./interaction.log",
    level: int = logging.INFO,
    max_bytes: int = 5 * 1024 * 1024,
    backup_count: int = 3,
) -> None:
    """Configure process logging to use a rotating file handler only.

    This removes default stdout/stderr handlers so the program writes logs
    only to a rotating log file. It also suppresses noisy third-party HTTP
    transport logs that are usually not useful during interactive RAG testing.
    """
    root_logger = logging.getLogger()
    for handler in list(root_logger.handlers):
        root_logger.removeHandler(handler)
        try:
            handler.close()
        except Exception:
            pass

    file_handler = RotatingFileHandler(
        log_path,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding="utf-8",
    )
    file_handler.setFormatter(
        logging.Formatter(
            "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
        )
    )

    root_logger.setLevel(level)
    root_logger.addHandler(file_handler)
    root_logger.propagate = False

    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("chromadb").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)


@dataclass(frozen=True)
class LLMConfig:
    """Configuration for the chat model.

    Attributes:
        model_name: Ollama model name for generation.
        base_url: Ollama server base URL.
        temperature: Sampling temperature for generation.
        system_prompt: Optional system prompt that defines assistant behavior.
        max_history_messages: Number of non-system messages to keep in memory.
    """

    model_name: str
    base_url: str
    temperature: float = 0.2
    system_prompt: Optional[str] = None
    max_history_messages: int = 12


@dataclass(frozen=True)
class EmbeddingConfig:
    """Configuration for the embedding model.

    Attributes:
        model_name: Ollama embedding model name.
        base_url: Ollama server base URL.
        query_prefix: Optional retrieval prefix for queries.
    """

    model_name: str
    base_url: str
    query_prefix: str = "search_query: "


@dataclass(frozen=True)
class VectorStoreConfig:
    """Configuration for a persistent Chroma vector store."""

    collection_name: str
    storage_path: str


@dataclass(frozen=True)
class RetrievalConfig:
    """Configuration for retrieval behavior.

    Attributes:
        enabled: Whether retrieval augmentation is enabled by default.
        top_k: Number of chunks to retrieve.
        max_context_chars: Hard cap for retrieved context text.
        score_threshold: Optional future hook; currently unused by Chroma wrapper.
        include_metadata: Whether to include metadata in the reference context.
    """

    enabled: bool = True
    top_k: int = 5
    max_context_chars: int = 4000
    score_threshold: Optional[float] = None
    include_metadata: bool = True


@dataclass
class AgentState:
    """Mutable state for a conversational RAG agent."""

    history: ChatMessageHistory = field(default_factory=ChatMessageHistory)


class RAGAgent:
    """Simple conversational RAG agent backed by Ollama + Chroma.

    Design goals:
    - keep chat history bounded
    - make retrieval optional per request
    - format references in a compact, grounded way
    - avoid coupling LLM config and embedding config
    """

    def __init__(
        self,
        *,
        llm_config: LLMConfig,
        embedding_config: EmbeddingConfig,
        vector_store_config: VectorStoreConfig,
        retrieval_config: RetrievalConfig | None = None,
    ) -> None:
        self.llm_config = llm_config
        self.embedding_config = embedding_config
        self.vector_store_config = vector_store_config
        self.retrieval_config = retrieval_config or RetrievalConfig()

        logger.info("Initializing chat model: %s", llm_config.model_name)
        self.llm = ChatOllama(
            model=llm_config.model_name,
            base_url=llm_config.base_url,
            temperature=llm_config.temperature,
        )

        logger.info(
            "Initializing embedding model: %s", embedding_config.model_name
        )
        self.embeddings = OllamaEmbeddings(
            model=embedding_config.model_name,
            base_url=embedding_config.base_url,
        )

        logger.info(
            "Opening Chroma collection '%s' at %s",
            vector_store_config.collection_name,
            vector_store_config.storage_path,
        )
        db_client = chromadb.PersistentClient(
            path=vector_store_config.storage_path
        )
        self.vectorstore = Chroma(
            client=db_client,
            embedding_function=self.embeddings,
            collection_name=vector_store_config.collection_name,
        )

        self.state = AgentState()
        if llm_config.system_prompt:
            self.state.history.add_message(
                SystemMessage(content=llm_config.system_prompt)
            )

    def _trim_history(self) -> None:
        """Keep the system message plus a bounded tail of conversation history."""
        messages = self.state.history.messages
        if not messages:
            return

        system_messages: List[BaseMessage] = [
            m for m in messages if isinstance(m, SystemMessage)
        ]
        non_system_messages: List[BaseMessage] = [
            m for m in messages if not isinstance(m, SystemMessage)
        ]
        if len(non_system_messages) <= self.llm_config.max_history_messages:
            return

        kept_non_system = non_system_messages[
            -self.llm_config.max_history_messages :
        ]
        self.state.history = ChatMessageHistory(
            messages=[*system_messages, *kept_non_system]
        )

    def _build_query(self, user_text: str) -> str:
        prefix = self.embedding_config.query_prefix or ""
        return f"{prefix}{user_text}" if prefix else user_text

    def _format_reference_block(self, docs: Iterable) -> str:
        """Format retrieved chunks into a compact reference section for the LLM."""
        parts: List[str] = []
        used_chars = 0

        for idx, doc in enumerate(docs, start=1):
            metadata = doc.metadata or {}
            header_bits: List[str] = [f"ref {idx}"]

            if self.retrieval_config.include_metadata:
                chunk_id = metadata.get("chunk_id")
                owned_span = metadata.get("owned_span")
                main_keyword = metadata.get("main_keyword")
                page = metadata.get("page")
                page_range = metadata.get("page_range")

                if chunk_id is not None:
                    header_bits.append(f"chunk={chunk_id}")
                if owned_span:
                    header_bits.append(f"span={owned_span}")
                if page_range:
                    header_bits.append(f"pages={page_range}")
                elif page is not None:
                    header_bits.append(f"page={page}")
                if main_keyword:
                    header_bits.append(f"topic={main_keyword}")

            snippet = (doc.page_content or "").strip()
            if not snippet:
                continue

            block = f"[{'; '.join(header_bits)}]\n{snippet}"
            if (
                used_chars + len(block)
                > self.retrieval_config.max_context_chars
            ):
                remaining = (
                    self.retrieval_config.max_context_chars - used_chars
                )
                if remaining <= 0:
                    break
                block = block[:remaining].rstrip()
                parts.append(block)
                break

            parts.append(block)
            used_chars += len(block)

        if not parts:
            return ""

        return (
            "Use the following references when relevant. Prefer them over unsupported claims.\n\n"
            + "\n\n".join(parts)
        )

    def _retrieve(self, user_text: str):
        """Run vector search and log a compact trace of returned references."""
        query = self._build_query(user_text)
        logger.info(
            "Running similarity search (k=%d)", self.retrieval_config.top_k
        )
        docs = self.vectorstore.similarity_search(
            query,
            k=self.retrieval_config.top_k,
        )
        logger.info("Vector store returned %d documents", len(docs))

        for idx, doc in enumerate(docs[: min(len(docs), 5)], start=1):
            metadata = doc.metadata or {}
            preview = doc.page_content or ""
            # preview = preview[:180] + ("..." if len(preview) > 180 else "")
            logger.info(
                "Retrieved ref %d | chunk_id=%s | span=%s | page=%s | page_range=%s | topic=%s | preview=%s",
                idx,
                metadata.get("chunk_id"),
                metadata.get("owned_span"),
                metadata.get("page"),
                metadata.get("page_range"),
                metadata.get("main_keyword"),
                preview,
            )

        return docs

    def respond(
        self, user_text: str, *, with_ref: Optional[bool] = None
    ) -> str:
        """Generate one assistant response.

        Args:
            user_text: User query text.
            with_ref: Optional override for retrieval behavior.
        """
        use_ref = (
            self.retrieval_config.enabled if with_ref is None else with_ref
        )

        reference_block = ""
        if use_ref:
            docs = self._retrieve(user_text)
            reference_block = self._format_reference_block(docs)

        prompt_content = (
            user_text
            if not reference_block
            else f"{reference_block}\n\nUser question:\n{user_text}"
        )

        self.state.history.add_message(HumanMessage(content=prompt_content))
        self._trim_history()

        logger.info("Invoking chat model")
        result = self.llm.invoke(self.state.history.messages)

        ai_message = (
            result
            if isinstance(result, AIMessage)
            else AIMessage(content=str(result))
        )
        self.state.history.add_message(ai_message)
        self._trim_history()
        return ai_message.content


def create_agent(
    llm_config: LLMConfig,
    embedding_config: EmbeddingConfig,
    vector_storage_config: VectorStoreConfig,
    retrieval_config: RetrievalConfig | None = None,
) -> Callable[[str], str]:
    """Backward-compatible factory that returns a callable responder."""
    agent = RAGAgent(
        llm_config=llm_config,
        embedding_config=embedding_config,
        vector_store_config=vector_storage_config,
        retrieval_config=retrieval_config,
    )
    return agent.respond


def main() -> None:
    """
    Interactive REPL for continuous RAG conversation.

    Commands:
        /quit, /exit        -> stop
        /clear              -> clear conversation history but keep system prompt
        /rag on             -> enable retrieval
        /rag off            -> disable retrieval
        /status             -> show current session settings
        /history            -> show current history length
    """
    configure_file_logging(
        log_path=f"./logs/interaction.{int(time.time())}.log",
        level=logging.INFO,
    )

    agent = RAGAgent(
        llm_config=LLMConfig(
            model_name="ministral-3:8b",
            base_url="http://ollama:11434",
            temperature=0.9,
            system_prompt=(
                "You are a philosophy mentor with a precise, serious, and reflective voice. "
                "You care about conceptual clarity, argumentative structure, and fidelity to source material. "
                "You speak in natural prose, as if discussing ideas with the user face to face.\n\n"
                "Answer clearly and directly, but do not oversimplify. "
                "When references are available, treat them as the primary evidence. "
                "Explain what they imply, what they do not imply, and where uncertainty remains.\n\n"
                "If a question is framed in a misleading way, do not answer it naively. "
                "Instead, gently reformulate it and explain the philosophical issue underneath it. "
                "If multiple traditions or positions are relevant, distinguish them carefully.\n\n"
                "Do not use bullet points, numbered lists, tables, or outline formatting. "
                "Write only in speech-like prose. "
                "Keep the response under 500 tokens. "
                "Prefer concise but thoughtful paragraphs. "
                "Do not include filler, generic encouragement, or meta-instructions."
            ),
            max_history_messages=10,
        ),
        embedding_config=EmbeddingConfig(
            model_name="nomic-embed-text-v2-moe:latest",
            base_url="http://ollama:11434",
            query_prefix="search_query: ",
        ),
        vector_store_config=VectorStoreConfig(
            collection_name="intro_to_philosophy",
            storage_path="./philosophy_db",
        ),
        retrieval_config=RetrievalConfig(
            enabled=True,
            top_k=10,
            max_context_chars=5000,
            include_metadata=True,
        ),
    )

    use_retrieval = agent.retrieval_config.enabled

    logger.info("Interactive RAG session started")

    print("RAG interactive session started.")
    print("Logs are written to ./interaction.log")
    print(
        "Commands: /quit, /exit, /clear, /rag on, /rag off, /status, /history"
    )

    # user_input = "Where is placed the mind of human in body?"

    # for it in range(20):
    #     answer = agent.respond(user_input, with_ref=use_retrieval)
    #     print("---------[", it, "Turns]---------", )
    #     print(answer)

    while True:
        try:
            user_input = input("\nYou> ").strip()
        except (EOFError, KeyboardInterrupt):
            logger.info("Interactive session ended by user interrupt")
            print("\nExiting.")
            break

        if not user_input:
            continue

        cmd = user_input.lower()

        if cmd in {"/quit", "/exit"}:
            logger.info("Interactive session ended by quit command")
            print("Exiting.")
            break

        if cmd == "/clear":
            system_messages = [
                m
                for m in agent.state.history.messages
                if isinstance(m, SystemMessage)
            ]
            agent.state.history = ChatMessageHistory(messages=system_messages)
            logger.info(
                "Conversation history cleared; system prompt preserved"
            )
            print("Conversation history cleared. System prompt preserved.")
            continue

        if cmd == "/rag on":
            use_retrieval = True
            logger.info("Retrieval enabled")
            print("Retrieval enabled.")
            continue

        if cmd == "/rag off":
            use_retrieval = False
            logger.info("Retrieval disabled")
            print("Retrieval disabled.")
            continue

        if cmd == "/status":
            status = (
                "Status:\n"
                f"  retrieval: {'on' if use_retrieval else 'off'}\n"
                f"  llm: {agent.llm_config.model_name}\n"
                f"  embeddings: {agent.embedding_config.model_name}\n"
                f"  collection: {agent.vector_store_config.collection_name}\n"
                f"  top_k: {agent.retrieval_config.top_k}\n"
                f"  max_context_chars: {agent.retrieval_config.max_context_chars}"
            )
            print(status)
            logger.info(
                "Status requested | retrieval=%s | llm=%s | embeddings=%s | collection=%s",
                use_retrieval,
                agent.llm_config.model_name,
                agent.embedding_config.model_name,
                agent.vector_store_config.collection_name,
            )
            continue

        if cmd == "/history":
            count = len(agent.state.history.messages)
            logger.info("History length requested | messages=%d", count)
            print(f"History messages: {count}")
            continue

        try:
            logger.info(
                "User query received | retrieval=%s | chars=%d",
                use_retrieval,
                len(user_input),
            )
            answer = agent.respond(user_input, with_ref=use_retrieval)
            logger.info("Assistant response generated | chars=%d", len(answer))
            print(f"\nAssistant> {answer}")
        except Exception as exc:
            logger.exception("Error during interaction")
            print(f"\n[error] {exc}")


if __name__ == "__main__":
    main()
