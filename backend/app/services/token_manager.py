from typing import List, Optional
import tiktoken
import logging

logger = logging.getLogger(__name__)

MODEL_CONTEXT_WINDOWS = {
    "llama-3.3-70b-versatile": 131_072,
    "llama-3.1-70b-versatile": 131_072,
    "llama-3.1-8b-instant": 131_072,
    "llama3-70b-8192": 8_192,
    "llama3-8b-8192": 8_192,
    "mixtral-8x7b-32768": 32_768,
    "gemma2-9b-it": 8_192,
}

DEFAULT_CONTEXT_WINDOW = 131_072


class TokenManager:
    def __init__(self, model: str = "llama-3.3-70b-versatile"):
        self.model = model
        self.encoding = tiktoken.get_encoding("cl100k_base")
        self.context_window = MODEL_CONTEXT_WINDOWS.get(model, DEFAULT_CONTEXT_WINDOW)

        self.budget = ContextBudget(
            total=self.context_window,
            system_prompt=2000,
            entry_context=4000,
            similar_entries=8000,
            goals=1000,
            recent_entries=4000,
            chat_history=16000,
            user_message=2000,
            response_buffer=4000,
        )

        logger.info(f"TokenManager initialized for {model} with {self.context_window:,} token context window")

    def count_tokens(self, text: str) -> int:
        if not text:
            return 0
        return len(self.encoding.encode(text))

    def count_messages_tokens(self, messages: List[dict]) -> int:
        total = 0
        for msg in messages:
            total += 4
            total += self.count_tokens(msg.get("role", ""))
            total += self.count_tokens(msg.get("content", ""))
        total += 2
        return total

    def truncate_to_tokens(self, text: str, max_tokens: int, suffix: str = "...") -> str:
        if not text:
            return text

        tokens = self.encoding.encode(text)
        if len(tokens) <= max_tokens:
            return text

        suffix_tokens = self.encoding.encode(suffix)
        available = max_tokens - len(suffix_tokens)

        if available <= 0:
            return suffix

        truncated_tokens = tokens[:available]
        return self.encoding.decode(truncated_tokens) + suffix

    def truncate_entries(
        self,
        entries: List[dict],
        max_total_tokens: int,
        content_key: str = "content",
        min_content_tokens: int = 200,
    ) -> List[dict]:
        if not entries:
            return entries

        entry_overhead = 50
        available_tokens = max_total_tokens
        result = []

        for entry in entries:
            if available_tokens <= entry_overhead + min_content_tokens:
                break

            entry_copy = entry.copy()
            content = entry_copy.get(content_key, "")
            content_tokens = self.count_tokens(content)

            max_content = available_tokens - entry_overhead

            if content_tokens > max_content:
                entry_copy[content_key] = self.truncate_to_tokens(
                    content,
                    max(min_content_tokens, max_content),
                    suffix="\n[Content truncated...]"
                )
                content_tokens = self.count_tokens(entry_copy[content_key])

            result.append(entry_copy)
            available_tokens -= (content_tokens + entry_overhead)

        logger.debug(f"Truncated {len(entries)} entries to {len(result)} within {max_total_tokens} tokens")
        return result

    def allocate_context_budget(
        self,
        system_prompt_tokens: int,
        chat_history_tokens: int,
        user_message_tokens: int,
    ) -> dict:
        used = system_prompt_tokens + chat_history_tokens + user_message_tokens
        available = self.context_window - used - self.budget.response_buffer

        if available < 1000:
            logger.warning(f"Very limited context available: {available} tokens")
            return {
                "entry_context": 0,
                "similar_entries": 0,
                "goals": 0,
                "recent_entries": 0,
            }

        allocations = {
            "entry_context": min(self.budget.entry_context, available * 0.2),
            "similar_entries": min(self.budget.similar_entries, available * 0.4),
            "goals": min(self.budget.goals, available * 0.1),
            "recent_entries": min(self.budget.recent_entries, available * 0.3),
        }

        total_allocated = sum(allocations.values())
        if total_allocated > available:
            scale = available / total_allocated
            allocations = {k: int(v * scale) for k, v in allocations.items()}

        logger.info(f"Context budget allocation: {allocations} (available: {available})")
        return {k: int(v) for k, v in allocations.items()}


class ContextBudget:
    def __init__(
        self,
        total: int,
        system_prompt: int = 2000,
        entry_context: int = 4000,
        similar_entries: int = 8000,
        goals: int = 1000,
        recent_entries: int = 4000,
        chat_history: int = 16000,
        user_message: int = 2000,
        response_buffer: int = 4000,
    ):
        self.total = total
        self.system_prompt = system_prompt
        self.entry_context = entry_context
        self.similar_entries = similar_entries
        self.goals = goals
        self.recent_entries = recent_entries
        self.chat_history = chat_history
        self.user_message = user_message
        self.response_buffer = response_buffer


token_manager = TokenManager()
