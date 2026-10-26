import pytest
from memory_manager import MemoryManager


def test_memory_crud():
    MemoryManager.clear_all_memories()
    assert len(MemoryManager.get_all_memories()) == 0

    m1 = MemoryManager.add_memory("User's favorite color is blue", category="preference")
    m2 = MemoryManager.add_memory("User lives in Seattle", category="fact")

    memories = MemoryManager.get_all_memories()
    assert len(memories) == 2

    search_res = MemoryManager.search_memories("Seattle")
    assert len(search_res) == 1
    assert search_res[0]["id"] == m2["id"]

    context = MemoryManager.get_formatted_memory_context()
    assert "PREFERENCE" in context
    assert "User's favorite color is blue" in context

    deleted = MemoryManager.delete_memory(m1["id"])
    assert deleted is True
    assert len(MemoryManager.get_all_memories()) == 1

    MemoryManager.clear_all_memories()
    assert len(MemoryManager.get_all_memories()) == 0
