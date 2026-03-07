from __future__ import annotations

from app.schemas import Record


class MemTable:
    """Teaching-oriented in-memory table based on Python dict."""

    def __init__(self) -> None:
        self._records: dict[str, Record] = {}
        self._size_bytes: int = 0

    @staticmethod
    def _estimate_record_bytes(record: Record) -> int:
        return len(record.key.encode("utf-8")) + len(record.value.encode("utf-8")) + 16

    def put(self, record: Record) -> None:
        old = self._records.get(record.key)
        if old is not None:
            self._size_bytes -= self._estimate_record_bytes(old)

        self._records[record.key] = record
        self._size_bytes += self._estimate_record_bytes(record)

    def get(self, key: str) -> str | None:
        record = self._records.get(key)
        if record is None:
            return None
        return record.value

    @property
    def size_records(self) -> int:
        return len(self._records)

    @property
    def size_bytes(self) -> int:
        return self._size_bytes
