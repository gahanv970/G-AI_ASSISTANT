from __future__ import annotations

import json
import logging
import os
import sys
import time
import uuid
from typing import Any

from config import _get_config_dir

logger = logging.getLogger(__name__)

MEMORY_FILE = "jarvis_memory.json"


class MemoryManager:
    """
    Manages JARVIS AI's long-term memory and context bank.
    Allows persisting facts, preferences, user details, and instructions,
    and retrieving them to inject into AI system prompts.
    """

    @classmethod
    def _get_memory_filepath(cls) -> str:
        return os.path.join(_get_config_dir(), MEMORY_FILE)

    @classmethod
    def get_all_memories(cls) -> list[dict[str, Any]]:
        """Loads and returns all stored memories."""
        path = cls._get_memory_filepath()
        if not os.path.exists(path):
            return []

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data if isinstance(data, list) else []
        except Exception as e:
            logger.error(f"Error loading memories from {path}: {e}")
            return []

    @classmethod
    def save_memories(cls, memories: list[dict[str, Any]]) -> bool:
        """Saves memory list to JSON file."""
        path = cls._get_memory_filepath()
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(memories, f, indent=4)
            return True
        except Exception as e:
            logger.error(f"Error saving memories to {path}: {e}")
            return False

    @classmethod
    def add_memory(cls, text: str, category: str = "general") -> dict[str, Any]:
        """Adds a new memory entry."""
        clean_text = text.strip()
        if not clean_text:
            raise ValueError("Memory text cannot be empty.")

        memories = cls.get_all_memories()
        entry = {
            "id": str(uuid.uuid4())[:8],
            "text": clean_text,
            "category": category.strip().lower() or "general",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        memories.append(entry)
        cls.save_memories(memories)
        logger.info(f"Added new memory [{entry['id']}]: '{clean_text}'")
        return entry

    @classmethod
    def delete_memory(cls, memory_id: str) -> bool:
        """Deletes a memory by ID."""
        memories = cls.get_all_memories()
        filtered = [m for m in memories if m.get("id") != memory_id]
        if len(filtered) < len(memories):
            cls.save_memories(filtered)
            logger.info(f"Deleted memory with ID {memory_id}")
            return True
        return False

    @classmethod
    def search_memories(cls, query: str) -> list[dict[str, Any]]:
        """Searches memories containing the query text."""
        q = query.strip().lower()
        if not q:
            return cls.get_all_memories()
        return [
            m for m in cls.get_all_memories()
            if q in m.get("text", "").lower() or q in m.get("category", "").lower()
        ]

    @classmethod
    def clear_all_memories(cls) -> bool:
        """Clears all stored memories."""
        return cls.save_memories([])

    @classmethod
    def get_formatted_memory_context(cls) -> str:
        """
        Formats memories into a prompt context block for AI queries.
        """
        memories = cls.get_all_memories()
        if not memories:
            return ""

        lines = ["[JARVIS LONG-TERM MEMORY & USER CONTEXT]"]
        for m in memories:
            lines.append(f"- ({m.get('category', 'general').upper()}) {m.get('text')}")

        return "\n".join(lines)
