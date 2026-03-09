from __future__ import annotations

import csv
import json
from pathlib import Path
from uuid import uuid4

from app.schemas import TraceEvent


class TraceEmitter:
    """Collects trace events and exports to stable JSON/CSV formats."""

    CSV_HEADER = ["event_id", "event_type", "timestamp", "seq", "payload_json"]

    def __init__(self) -> None:
        self.events: list[TraceEvent] = []

    def emit(self, event_type: str, seq: int, payload: dict) -> TraceEvent:
        event = TraceEvent(
            event_id=str(uuid4()),
            event_type=event_type,
            seq=seq,
            payload=payload,
        )
        self.events.append(event)
        return event

    def export_json(self, file_path: str) -> str:
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = [event.model_dump(mode="json") for event in self.events]
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return str(path)

    def export_csv(self, file_path: str) -> str:
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        with path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=self.CSV_HEADER)
            writer.writeheader()
            for event in self.events:
                writer.writerow(
                    {
                        "event_id": event.event_id,
                        "event_type": event.event_type,
                        "timestamp": event.timestamp.isoformat(),
                        "seq": event.seq,
                        "payload_json": json.dumps(event.payload, ensure_ascii=False, sort_keys=True),
                    }
                )

        return str(path)
