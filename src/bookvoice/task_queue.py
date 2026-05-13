import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .onboarding import default_state_dir


PENDING = "pending"
RUNNING = "running"
COMPLETED = "completed"
FAILED = "failed"
CANCELED = "canceled"
STATUSES = (PENDING, RUNNING, COMPLETED, FAILED, CANCELED)
TASK_QUEUE_FILENAME = "task_queue.json"


@dataclass
class QueueItem:
    path: str
    status: str = PENDING


class TaskQueue:
    def __init__(self) -> None:
        self.items: list[QueueItem] = []

    def add_many(self, paths: list[str]) -> int:
        existing = {item.path for item in self.items}
        added_count = 0
        for path in paths:
            if path in existing:
                continue
            self.items.append(QueueItem(path=path))
            existing.add(path)
            added_count += 1
        return added_count

    def clear(self) -> None:
        self.items.clear()

    def paths(self) -> tuple[str, ...]:
        return tuple(item.path for item in self.items)

    def pending_paths(self) -> tuple[str, ...]:
        return tuple(item.path for item in self.items if item.status == PENDING)

    def next_pending(self) -> str | None:
        for item in self.items:
            if item.status == PENDING:
                return item.path
        return None

    def mark_running(self, path: str) -> None:
        self._mark(path, RUNNING)

    def mark_completed(self, path: str) -> None:
        self._mark(path, COMPLETED)

    def mark_failed(self, path: str) -> None:
        self._mark(path, FAILED)

    def mark_canceled(self, path: str) -> None:
        self._mark(path, CANCELED)

    def status(self, path: str) -> str | None:
        for item in self.items:
            if item.path == path:
                return item.status
        return None

    def status_counts(self) -> dict[str, int]:
        counts = {status: 0 for status in STATUSES}
        for item in self.items:
            if item.status in counts:
                counts[item.status] += 1
        return counts

    def to_records(self) -> list[dict[str, str]]:
        return [asdict(item) for item in self.items]

    @classmethod
    def from_records(
        cls,
        records: list[dict[str, Any]],
        *,
        resume_interrupted: bool = True,
    ) -> "TaskQueue":
        queue = cls()
        seen: set[str] = set()
        for record in records:
            if not isinstance(record, dict):
                continue
            path = record.get("path")
            if not isinstance(path, str) or not path.strip() or path in seen:
                continue
            status = record.get("status")
            if status not in STATUSES:
                status = PENDING
            if resume_interrupted and status == RUNNING:
                status = PENDING
            queue.items.append(QueueItem(path=path, status=status))
            seen.add(path)
        return queue

    def _mark(self, path: str, status: str) -> None:
        for item in self.items:
            if item.path == path:
                item.status = status
                return


def task_queue_state_path(state_dir: Path | None = None) -> Path:
    return (state_dir or default_state_dir()) / TASK_QUEUE_FILENAME


def load_task_queue(state_dir: Path | None = None) -> TaskQueue:
    path = task_queue_state_path(state_dir)
    if not path.exists():
        return TaskQueue()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, TypeError):
        return TaskQueue()
    if not isinstance(data, list):
        return TaskQueue()
    return TaskQueue.from_records(data)


def save_task_queue(queue: TaskQueue, state_dir: Path | None = None) -> None:
    path = task_queue_state_path(state_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(queue.to_records(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
