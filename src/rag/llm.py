"""Anthropic LLM client with strict grounding for AgriSense RAG."""

from __future__ import annotations

import os
from typing import Any

FALLBACK_ANSWER = "I don't have enough information from the available data."

SYSTEM_PROMPT = """You are an AgriSense agricultural assistant for big onion yield prediction in Sri Lanka.

Rules:
1. Answer ONLY using the retrieved context provided by the user message.
2. Do NOT use any outside or general agricultural knowledge.
3. If the retrieved context does not contain enough information to answer the question, reply with exactly:
"I don't have enough information from the available data."
4. Be concise and cite specific numbers or feature names from the context when available.
5. Focus on predictions, SHAP explanations, uncertainty intervals, and cultivation facts present in the context."""


class AnthropicClient:
    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
    ) -> None:
        self.api_key = api_key or os.environ.get('ANTHROPIC_API_KEY', '')
        self.model = model or os.environ.get(
            'ANTHROPIC_MODEL', 'claude-3-5-haiku-latest'
        )
        if not self.api_key:
            raise ValueError(
                'ANTHROPIC_API_KEY environment variable is not set.'
            )

    def generate(self, question: str, context_chunks: list[dict[str, Any]]) -> str:
        import anthropic

        if not context_chunks:
            return FALLBACK_ANSWER

        context_block = '\n\n---\n\n'.join(
            f"[{c.get('source_type', 'UNKNOWN')}] {c.get('content', '')}"
            for c in context_chunks
        )
        user_message = (
            f"Question: {question}\n\n"
            f"Retrieved context:\n{context_block}\n\n"
            "Answer the question using only the retrieved context above."
        )

        client = anthropic.Anthropic(api_key=self.api_key)
        response = client.messages.create(
            model=self.model,
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            messages=[{'role': 'user', 'content': user_message}],
        )

        text_parts = [
            block.text
            for block in response.content
            if hasattr(block, 'text')
        ]
        return '\n'.join(text_parts).strip() or FALLBACK_ANSWER
