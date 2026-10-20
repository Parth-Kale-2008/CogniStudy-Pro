"""
Conversational State and Multi-Turn Memory Service.
"""

from typing import Dict, List, Optional
from collections import defaultdict
from app.models.schemas import StudyMode

class ChatSessionService:
    """
    Manages in-memory conversation histories and active study modes per user.
    """

    def __init__(self, max_history_turns: int = 6):
        self.max_history_turns = max_history_turns
        self._history: Dict[str, List[Dict[str, str]]] = defaultdict(list)
        self._modes: Dict[str, StudyMode] = defaultdict(lambda: StudyMode.STUDENT)

    def get_mode(self, user_id: str) -> StudyMode:
        return self._modes[user_id]

    def set_mode(self, user_id: str, mode: StudyMode) -> StudyMode:
        self._modes[user_id] = mode
        return mode

    def add_turn(self, user_id: str, question: str, answer: str) -> None:
        user_history = self._history[user_id]
        user_history.append({"role": "user", "content": question})
        user_history.append({"role": "assistant", "content": answer})
        if len(user_history) > self.max_history_turns * 2:
            self._history[user_id] = user_history[-(self.max_history_turns * 2):]

    def get_history(self, user_id: str) -> List[Dict[str, str]]:
        return self._history.get(user_id, [])

    def clear_history(self, user_id: str) -> None:
        if user_id in self._history:
            del self._history[user_id]


chat_service = ChatSessionService()
