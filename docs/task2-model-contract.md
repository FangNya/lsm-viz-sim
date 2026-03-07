# Task 2: Unified Data Model and Interface Contract

This document defines shared contracts for the teaching-oriented LSM-Tree simulator backend.
Current scope only includes model definitions and validation rules.

## Model Locations

- API and serializable contract models: `backend/app/schemas/models.py`
- Internal runtime state dataclasses: `backend/app/core/state.py`

## Serialization Contract

- Pydantic models use `model_dump(mode="json")` for stable JSON export.
- Dataclass state models provide explicit `to_dict()` / `from_dict()` helpers.
- Enums are serialized as lowercase string values:
  - `compaction_strategy`: `stc` or `lcs`
  - `op`: `put`

## Default Rules

- `LSMConfig` provides safe teaching defaults (positive sizes, 4 levels, STC strategy).
- `Record`/`WALRecord`/`WorkloadOperation` default `op=put`.
- `timestamp` and `created_at` default to UTC current time.
- `MetricsSnapshot` defaults all counters to zero, amplification to 1.0.

## Validation Rules

- Positive integer constraints for memtable and size-related fields.
- Non-negative constraints for counters, sequence numbers, and level indexes.
- Enum constraints for compaction strategy and operation type.