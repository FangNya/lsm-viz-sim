from __future__ import annotations

import argparse
import csv
import json
import shutil
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.append(str(BACKEND))

from app.core import LSMSimulator
from app.schemas import LSMConfig

WORKLOADS_DIR = ROOT / "experiments" / "workloads"
PROFILES_PATH = ROOT / "experiments" / "config_profiles.json"
DEFAULT_WORKLOADS = [
    "final_sequential_ingest",
    "final_hotspot_overwrite",
    "final_overlap_waves",
    "final_mixed_read_validation",
]
DEFAULT_PROFILES = [
    "final_balanced",
    "final_dense_compaction",
    "final_overlap_sensitive",
]


def load_workload(path: Path) -> tuple[list[dict[str, Any]], str]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, list):
        return payload, ""
    if isinstance(payload, dict) and isinstance(payload.get("operations"), list):
        description = str(payload.get("description", ""))
        return payload["operations"], description
    raise ValueError("workload JSON must be a list or an object with an operations list")


def load_profiles(path: Path) -> dict[str, dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("config profiles JSON must be an object keyed by profile name")
    return {str(name): dict(config) for name, config in payload.items()}


def run_workload(sim: LSMSimulator, workload: list[dict[str, Any]]) -> dict[str, Any]:
    oracle: dict[str, str] = {}
    put_count = 0
    get_count = 0
    correct_gets = 0
    mismatches: list[dict[str, Any]] = []

    for item in workload:
        op = item.get("op")
        if op == "put":
            result = sim.put(str(item["key"]), str(item["value"]))
            oracle[str(item["key"])] = str(item["value"])
            put_count += 1
            if result.needs_flush:
                sim.flush_memtable()
        elif op == "get":
            key = str(item["key"])
            expected_value = oracle.get(key)
            expected_found = expected_value is not None
            result = sim.get(key)
            get_count += 1

            if result.found == expected_found and result.value == expected_value:
                correct_gets += 1
            else:
                mismatches.append(
                    {
                        "key": key,
                        "expected_found": expected_found,
                        "expected_value": expected_value,
                        "actual_found": result.found,
                        "actual_value": result.value,
                        "source": result.source,
                        "level": result.level,
                        "table_id": result.table_id,
                    }
                )
        else:
            raise ValueError(f"unsupported op: {op}")

    if sim.memtable.size_records > 0:
        sim.flush_memtable()

    return {
        "put_count": put_count,
        "get_count": get_count,
        "correct_gets": correct_gets,
        "mismatch_count": len(mismatches),
        "validation_accuracy": (correct_gets / get_count) if get_count > 0 else 0.0,
        "mismatches": mismatches[:20],
        "final_oracle_key_count": len(oracle),
    }


def summarize(sim: LSMSimulator, validation: dict[str, Any]) -> dict[str, Any]:
    levels = sim.list_levels()
    counts = {level: len(tables) for level, tables in levels.items()}
    snapshot = sim.metrics.snapshot
    non_empty_levels = [
        int(level_name.split("_")[-1])
        for level_name, tables in levels.items()
        if tables
    ]
    return {
        "put_count": validation["put_count"],
        "get_count": validation["get_count"],
        "correct_gets": validation["correct_gets"],
        "mismatch_count": validation["mismatch_count"],
        "validation_accuracy": validation["validation_accuracy"],
        "final_oracle_key_count": validation["final_oracle_key_count"],
        "flush_count": snapshot.flush_count,
        "compaction_count": snapshot.compaction_count,
        "sstable_count_by_level": counts,
        "max_level_with_data": max(non_empty_levels) if non_empty_levels else -1,
        "read_amplification": snapshot.read_amplification,
        "write_amplification": snapshot.write_amplification,
        "logical_write_bytes_total": snapshot.logical_write_bytes_total,
        "actual_disk_write_bytes_total": snapshot.actual_disk_write_bytes_total,
        "user_query_read_io_total": snapshot.user_query_read_io_total,
    }


def export_summary_csv(rows: list[dict[str, Any]], path: Path) -> None:
    headers = [
        "workload",
        "profile",
        "strategy",
        "operation_count",
        "put_count",
        "get_count",
        "correct_gets",
        "mismatch_count",
        "validation_accuracy",
        "final_oracle_key_count",
        "flush_count",
        "compaction_count",
        "sstable_count_by_level",
        "max_level_with_data",
        "read_amplification",
        "write_amplification",
        "logical_write_bytes_total",
        "actual_disk_write_bytes_total",
        "user_query_read_io_total",
    ]
    with path.open("w", newline="", encoding="utf-8") as file_obj:
        writer = csv.DictWriter(file_obj, fieldnames=headers)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def build_config(
    profile_name: str,
    profile_config: dict[str, Any],
    strategy: str,
    wal_dir: Path,
    data_dir: Path,
) -> LSMConfig:
    config_values = {
        **profile_config,
        "compaction_strategy": strategy,
        "wal_dir": str(wal_dir),
        "data_dir": str(data_dir),
    }
    return LSMConfig(**config_values)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workloads", nargs="*", default=DEFAULT_WORKLOADS)
    parser.add_argument("--profiles", nargs="*", default=DEFAULT_PROFILES)
    parser.add_argument("--out", default=str(ROOT / "experiments" / "output"))
    args = parser.parse_args()

    profiles = load_profiles(PROFILES_PATH)
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    summary_rows: list[dict[str, Any]] = []
    summary_json: list[dict[str, Any]] = []

    for workload_name in args.workloads:
        workload_path = WORKLOADS_DIR / f"{workload_name}.json"
        workload, workload_description = load_workload(workload_path)

        for profile_name in args.profiles:
            if profile_name not in profiles:
                raise ValueError(f"unknown profile: {profile_name}")
            profile_config = profiles[profile_name]

            for strategy in ["stc", "lcs"]:
                run_dir = out_dir / workload_name / profile_name / strategy
                if run_dir.exists():
                    shutil.rmtree(run_dir)
                data_dir = run_dir / "data"
                wal_dir = run_dir / "wal"
                run_dir.mkdir(parents=True, exist_ok=True)

                config = build_config(profile_name, profile_config, strategy, wal_dir, data_dir)
                (run_dir / "config.json").write_text(
                    json.dumps(config.model_dump(mode="json"), ensure_ascii=False, indent=2),
                    encoding="utf-8",
                )

                sim = LSMSimulator(config)
                validation = run_workload(sim, workload)

                metrics_json = sim.export_metrics_json(str(run_dir / "metrics.json"))
                metrics_csv = sim.export_metrics_csv(str(run_dir / "metrics.csv"))
                trace_json = sim.export_trace_json(str(run_dir / "trace.json"))
                trace_csv = sim.export_trace_csv(str(run_dir / "trace.csv"))
                validation_json_path = run_dir / "validation.json"
                validation_json_path.write_text(
                    json.dumps(validation, ensure_ascii=False, indent=2),
                    encoding="utf-8",
                )

                summary = summarize(sim, validation)
                summary_record = {
                    "workload": workload_name,
                    "profile": profile_name,
                    "strategy": strategy,
                    "operation_count": len(workload),
                    **summary,
                }
                summary_rows.append(
                    {
                        **summary_record,
                        "sstable_count_by_level": json.dumps(
                            summary_record["sstable_count_by_level"],
                            ensure_ascii=False,
                            sort_keys=True,
                        ),
                    }
                )
                summary_json.append(
                    {
                        **summary_record,
                        "workload_description": workload_description,
                        "profile_config": profile_config,
                        "artifacts": {
                            "config_json": str(run_dir / "config.json"),
                            "metrics_json": metrics_json,
                            "metrics_csv": metrics_csv,
                            "trace_json": trace_json,
                            "trace_csv": trace_csv,
                            "validation_json": str(validation_json_path),
                        },
                        "validation": validation,
                    }
                )

    (out_dir / "summary.json").write_text(
        json.dumps(summary_json, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    export_summary_csv(summary_rows, out_dir / "summary.csv")


if __name__ == "__main__":
    main()
