from pathlib import Path
import time
from threading import Lock

# Global registry to track loggers by session
_loggers = {}
_lock = Lock()


class MarkdownLogger:
    def __init__(self, session_id: str, base_dir: Path = Path("./markdown_logs"), agent_name: str = "agent"):
        self.session_id = session_id
        self.agent_name = agent_name
        self.timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        self.file_path = base_dir / f"session_{session_id}.md"

        # Ensure base directory exists
        base_dir.mkdir(parents=True, exist_ok=True)

        self._lock = Lock()
        self._init_file()

    def _init_file(self):
        with self._lock, open(self.file_path, "w", encoding="utf-8") as f:
            f.write(f"# Session Log: {self.session_id}\n")
            f.write(f"**Agent**: {self.agent_name}  \n")
            f.write(f"**Started At**: {self.timestamp}  \n\n")
            f.write("---\n\n")

    def write(self, title: str, content: str):
        with self._lock, open(self.file_path, "a", encoding="utf-8") as f:
            f.write(f"## {title}\n")
            f.write(str(content).strip() + "\n\n---\n\n")

    def get_path(self):
        return self.file_path


def set_session_id(session_id: str, agent_name: str = "agent"):
    with _lock:
        _loggers[session_id] = MarkdownLogger(session_id=session_id, agent_name=agent_name)


def get_markdown_logger(session_id: str) -> MarkdownLogger:
    with _lock:
        if session_id not in _loggers:
            raise ValueError(f"No MarkdownLogger initialized for session: {session_id}")
        return _loggers[session_id]