from dataclasses import dataclass


PENDING = "pending"
RUNNING = "running"
COMPLETED = "completed"
FAILED = "failed"
CANCELED = "canceled"
STATUSES = (PENDING, RUNNING, COMPLETED, FAILED, CANCELED)


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

    def _mark(self, path: str, status: str) -> None:
        for item in self.items:
            if item.path == path:
                item.status = status
                return
