from __future__ import annotations

from app.schemas import Record


class MemTable:
    """Teaching-oriented in-memory table with per-key version lists."""

    def __init__(self) -> None:
        self._records: dict[str, list[Record]] = {}
        self._size_bytes: int = 0

    @staticmethod
    def _estimate_record_bytes(record: Record) -> int:
        return len(record.key.encode("utf-8")) + len(record.value.encode("utf-8")) + 16

    def put(self, record: Record) -> None:
        self._records.setdefault(record.key, []).append(record)
        self._size_bytes += self._estimate_record_bytes(record)

    def get(self, key: str) -> str | None:
        versions = self._records.get(key)
        if not versions:
            return None
        return versions[-1].value

    def sorted_records(self) -> list[Record]:
        ordered: list[Record] = []
        for key in sorted(self._records.keys()):
            versions = sorted(self._records[key], key=lambda record: record.seq, reverse=True)
            ordered.extend(versions)
        return ordered

    def clear(self) -> None:
        self._records.clear()
        self._size_bytes = 0

    @property
    def size_records(self) -> int:
        return sum(len(versions) for versions in self._records.values())

    @property
    def size_bytes(self) -> int:
        return self._size_bytes
