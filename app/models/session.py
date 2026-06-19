import uuid
import json
import os
from datetime import datetime
from config import Config


class AssessmentSession:
    """管理一次完整评估的会话状态"""

    def __init__(self):
        self.session_id = str(uuid.uuid4())[:8]
        self.created_at = datetime.now().isoformat()
        self.current_phase = 1
        self.current_instrument = None
        self.current_item_index = 0
        self.completed_instruments = []
        self.phase_instruments = []  # 当前阶段的量表列表
        self.responses = {}  # item_id -> score
        self.phase1_scores = None
        self.all_scores = None
        self.open_text_responses = {}  # question_id -> text
        self.is_complete = False

    def to_dict(self):
        return {
            "session_id": self.session_id,
            "created_at": self.created_at,
            "current_phase": self.current_phase,
            "current_instrument": self.current_instrument,
            "current_item_index": self.current_item_index,
            "completed_instruments": self.completed_instruments,
            "phase_instruments": self.phase_instruments,
            "responses": self.responses,
            "phase1_scores": self.phase1_scores,
            "all_scores": self.all_scores,
            "open_text_responses": self.open_text_responses,
            "is_complete": self.is_complete,
        }

    @classmethod
    def from_dict(cls, data):
        s = cls.__new__(cls)
        s.session_id = data["session_id"]
        s.created_at = data["created_at"]
        s.current_phase = data["current_phase"]
        s.current_instrument = data["current_instrument"]
        s.current_item_index = data["current_item_index"]
        s.completed_instruments = data["completed_instruments"]
        s.phase_instruments = data.get("phase_instruments", [])
        s.responses = data["responses"]
        s.phase1_scores = data["phase1_scores"]
        s.all_scores = data["all_scores"]
        s.open_text_responses = data.get("open_text_responses", {})
        s.is_complete = data["is_complete"]
        return s


class SessionManager:
    """服务端会话管理器（内存 + 文件持久化）"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._sessions = {}
            cls._instance._load_from_disk()
        return cls._instance

    def _get_storage_path(self):
        return os.path.join(Config.DATA_DIR, "sessions.json")

    def _load_from_disk(self):
        path = self._get_storage_path()
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for sid, sdata in data.items():
                        self._sessions[sid] = AssessmentSession.from_dict(sdata)
            except (json.JSONDecodeError, KeyError):
                pass

    def _save_to_disk(self):
        path = self._get_storage_path()
        data = {sid: s.to_dict() for sid, s in self._sessions.items()}
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def create_session(self):
        session = AssessmentSession()
        self._sessions[session.session_id] = session
        self._save_to_disk()
        return session

    def get_session(self, session_id):
        return self._sessions.get(session_id)

    def save_session(self, session):
        self._sessions[session.session_id] = session
        self._save_to_disk()

    def delete_session(self, session_id):
        if session_id in self._sessions:
            del self._sessions[session_id]
            self._save_to_disk()
