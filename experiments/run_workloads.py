from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.append(str(BACKEND))

from app.core import LSMSimulator
from app.schemas import LSMConfig


def load_workload(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError("workload JSON must be a list")
    return payload


def run_workload(sim: LSMSimulator, workload: list[dict[str, Any]]) -> None:
    for item in workload:
        op = item.get("op")
        if op == "put":
            key = str(item["key"])
            value = str(item["value"])
            result = sim.put(key, value)
            if result.needs_flush:
                sim.flush_memtable()
        elif op == "get":
            sim.get(str(item["key"]))
        else:
            raise ValueError(f"unsupported op: {op}")

    # Ensure tail memtable is flushed for reproducible SSTable counts.
    if sim.memtable.size_records > 0:
        sim.flush_memtable()


def summarize(sim: LSMSimulator) -> dict[str, Any]:
    levels = sim.list_levels()
    counts = {k: len(v) for k, v in levels.items()}
    snapshot = sim.metrics.snapshot
    return {
        "flush_count": snapshot.flush_count,
        "compaction_count": snapshot.compaction_count,
        "sstable_count_by_level": counts,
        "read_amplification": snapshot.read_amplification,
        "write_amplification": snapshot.write_amplification,
    }


def export_summary_csv(rows: list[dict[str, Any]], path: Path) -> None:
    headers = [
        "workload",
        "strategy",
        "flush_count",
        "compaction_count",
        "sstable_count_by_level",
        "read_amplification",
        "write_amplification",
    ]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workloads", nargs="*", default=["write_heavy", "mixed_read_write"])
    parser.add_argument("--out", default=str(ROOT / "experiments" / "output"))
    args = parser.parse_args()

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    summary_rows: list[dict[str, Any]] = []
    summary_json: list[dict[str, Any]] = []

    for workload_name in args.workloads:
        workload_path = ROOT / "experiments" / "workloads" / f"{workload_name}.json"
        workload = load_workload(workload_path)

        for strategy in ["stc", "lcs"]:
            run_dir = out_dir / workload_name / strategy
            data_dir = run_dir / "data"
            wal_dir = run_dir / "wal"
            run_dir.mkdir(parents=True, exist_ok=True)

            config = LSMConfig(
                memtable_max_records=8,
                memtable_max_bytes=4096,
                max_levels=4,
                compaction_strategy=strategy,
                stc_trigger_tables=3,
                l0_compaction_trigger_tables=3,
                level_size_multiplier=10.0,
                bloom_bits_per_key=10,
                wal_dir=str(wal_dir),
                data_dir=str(data_dir),
            )
            sim = LSMSimulator(config)
            run_workload(sim, workload)

            metrics_json = sim.export_metrics_json(str(run_dir / "metrics.json"))
            metrics_csv = sim.export_metrics_csv(str(run_dir / "metrics.csv"))
            trace_json = sim.export_trace_json(str(run_dir / "trace.json"))
            trace_csv = sim.export_trace_csv(str(run_dir / "trace.csv"))

            summary = summarize(sim)
            summary_record = {
                "workload": workload_name,
                "strategy": strategy,
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
                    "artifacts": {
                        "metrics_json": metrics_json,
                        "metrics_csv": metrics_csv,
                        "trace_json": trace_json,
                        "trace_csv": trace_csv,
                    },
                }
            )

    (out_dir / "summary.json").write_text(
        json.dumps(summary_json, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    export_summary_csv(summary_rows, out_dir / "summary.csv")


if __name__ == "__main__":
    main()
