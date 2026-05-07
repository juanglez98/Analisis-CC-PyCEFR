#!/usr/bin/env python3
"""Compare complexity JSON outputs from PyCEFR and radon (cc mode).

Example:
    python src/generator.py --pycefr pycefr.json --radon radon.json --output report.json
"""

from __future__ import annotations

import argparse
import json
import os
import time
from pathlib import Path
from typing import Any

COMPLEXITY_KEYS = ("complexity", "cyclomatic_complexity", "cc", "score")
NAME_KEYS = ("name", "function", "method", "qualified_name", "id", "symbol")
FILE_KEYS = ("file", "filename", "path", "module", "source")
LINE_KEYS = ("lineno", "line", "start_line")
TYPE_KEYS = ("type", "kind", "category", "node_type")
RANK_KEYS = ("rank", "grade")
DEBUG_LOG_PATH = "/home/juan/Documents/Analisis-CC-PyCEFR/.cursor/debug-af0a20.log"
DEBUG_SESSION_ID = "af0a20"


def debug_log(run_id: str, hypothesis_id: str, location: str, message: str, data: dict[str, Any]) -> None:
    payload = {
        "sessionId": DEBUG_SESSION_ID,
        "runId": run_id,
        "hypothesisId": hypothesis_id,
        "location": location,
        "message": message,
        "data": data,
        "timestamp": int(time.time() * 1000),
    }
    try:
        with open(DEBUG_LOG_PATH, "a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, ensure_ascii=False) + "\n")
    except OSError:
        # Debug logging must never break the actual command.
        pass


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Read two JSON reports (PyCEFR and radon cc) and compare complexity "
            "results by function/method."
        )
    )
    parser.add_argument("--pycefr", required=True, help="Path to PyCEFR JSON output.")
    parser.add_argument("--radon", required=True, help="Path to radon -j cc JSON output.")
    parser.add_argument(
        "--output",
        help="Optional path to write a machine-readable comparison report JSON.",
    )
    parser.add_argument(
        "--show-matches",
        action="store_true",
        help="Also print entries where complexity is equal.",
    )
    return parser.parse_args()


def read_json(path: str) -> Any:
    candidate_path = Path(path)
    resolved_path = candidate_path if candidate_path.is_absolute() else (Path.cwd() / candidate_path)
    nearby_json = []
    if resolved_path.parent.exists():
        nearby_json = sorted(
            [item.name for item in resolved_path.parent.iterdir() if item.suffix.lower() == ".json"]
        )[:20]

    run_id = f"run-{int(time.time() * 1000)}"

    # region agent log
    debug_log(
        run_id=run_id,
        hypothesis_id="H1",
        location="src/generator.py:read_json:entry",
        message="Attempting to read JSON file",
        data={
            "input_path": path,
            "cwd": str(Path.cwd()),
            "resolved_path": str(resolved_path),
            "exists": resolved_path.exists(),
            "is_file": resolved_path.is_file(),
            "nearby_json": nearby_json,
        },
    )
    # endregion

    try:
        with open(path, "r", encoding="utf-8") as handle:
            content = json.load(handle)
    except FileNotFoundError:
        # region agent log
        debug_log(
            run_id=run_id,
            hypothesis_id="H2",
            location="src/generator.py:read_json:file_not_found",
            message="JSON file not found while opening path",
            data={
                "input_path": path,
                "resolved_path": str(resolved_path),
                "cwd": str(Path.cwd()),
                "nearby_json": nearby_json,
            },
        )
        # endregion
        raise
    except json.JSONDecodeError as error:
        # region agent log
        debug_log(
            run_id=run_id,
            hypothesis_id="H3",
            location="src/generator.py:read_json:json_decode_error",
            message="JSON decode failed",
            data={
                "input_path": path,
                "resolved_path": str(resolved_path),
                "error": str(error),
            },
        )
        # endregion
        raise
    except OSError as error:
        # region agent log
        debug_log(
            run_id=run_id,
            hypothesis_id="H4",
            location="src/generator.py:read_json:os_error",
            message="OS error while opening JSON file",
            data={
                "input_path": path,
                "resolved_path": str(resolved_path),
                "error": str(error),
            },
        )
        # endregion
        raise

    # region agent log
    debug_log(
        run_id=run_id,
        hypothesis_id="H5",
        location="src/generator.py:read_json:success",
        message="JSON file loaded successfully",
        data={
            "input_path": path,
            "resolved_path": str(resolved_path),
            "top_level_type": type(content).__name__,
        },
    )
    # endregion
    return content


def as_number(value: Any) -> float | None:
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value.strip())
        except ValueError:
            return None
    return None


def pick_first(data: dict[str, Any], keys: tuple[str, ...]) -> Any:
    for key in keys:
        if key in data:
            return data[key]
    return None


def looks_like_path_key(key: str) -> bool:
    return "/" in key or key.endswith(".py")


def normalize_record(item: dict[str, Any], source: str, inherited_file: str | None) -> dict[str, Any] | None:
    raw_complexity = pick_first(item, COMPLEXITY_KEYS)
    complexity = as_number(raw_complexity)
    if complexity is None:
        return None

    name = pick_first(item, NAME_KEYS)
    line = pick_first(item, LINE_KEYS)
    kind = pick_first(item, TYPE_KEYS)
    rank = pick_first(item, RANK_KEYS)
    file_name = pick_first(item, FILE_KEYS) or inherited_file

    return {
        "source": source,
        "file": str(file_name) if file_name is not None else "<unknown>",
        "name": str(name) if name is not None else "<anonymous>",
        "line": int(line) if isinstance(line, int) else None,
        "type": str(kind) if kind is not None else None,
        "rank": str(rank) if rank is not None else None,
        "complexity": complexity,
        "raw": item,
    }


def extract_records(data: Any, source: str) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []

    # Fast path for canonical radon cc -j output: { "file.py": [ {...}, ... ] }
    if isinstance(data, dict):
        is_canonical_radon = True
        for value in data.values():
            if not isinstance(value, list):
                is_canonical_radon = False
                break
            if not all(isinstance(entry, dict) for entry in value):
                is_canonical_radon = False
                break

        if is_canonical_radon:
            for file_name, entries in data.items():
                for entry in entries:
                    normalized = normalize_record(entry, source, inherited_file=file_name)
                    if normalized:
                        records.append(normalized)
            return records

    def walk(node: Any, inherited_file: str | None = None) -> None:
        if isinstance(node, dict):
            normalized = normalize_record(node, source, inherited_file)
            if normalized:
                records.append(normalized)

            for key, value in node.items():
                next_file = inherited_file
                if isinstance(key, str) and looks_like_path_key(key):
                    next_file = key
                if key in FILE_KEYS and isinstance(value, str):
                    next_file = value
                walk(value, next_file)
            return

        if isinstance(node, list):
            for item in node:
                walk(item, inherited_file)

    walk(data)
    return records


def make_key(record: dict[str, Any]) -> tuple[str, str, int | None, str | None]:
    return (
        record["file"],
        record["name"],
        record["line"],
        record["type"],
    )


def index_records(records: list[dict[str, Any]]) -> dict[tuple[str, str, int | None, str | None], dict[str, Any]]:
    indexed: dict[tuple[str, str, int | None, str | None], dict[str, Any]] = {}
    for record in records:
        key = make_key(record)
        if key not in indexed:
            indexed[key] = record
    return indexed


def compare(pycefr_records: list[dict[str, Any]], radon_records: list[dict[str, Any]]) -> dict[str, Any]:
    py_map = index_records(pycefr_records)
    rd_map = index_records(radon_records)

    keys = sorted(set(py_map.keys()) | set(rd_map.keys()))

    only_pycefr = []
    only_radon = []
    mismatches = []
    matches = []

    for key in keys:
        py = py_map.get(key)
        rd = rd_map.get(key)

        if py and not rd:
            only_pycefr.append(py)
            continue
        if rd and not py:
            only_radon.append(rd)
            continue

        py_cc = py["complexity"]
        rd_cc = rd["complexity"]
        delta = py_cc - rd_cc
        item = {
            "key": {
                "file": key[0],
                "name": key[1],
                "line": key[2],
                "type": key[3],
            },
            "pycefr_complexity": py_cc,
            "radon_complexity": rd_cc,
            "delta": delta,
            "pycefr_rank": py.get("rank"),
            "radon_rank": rd.get("rank"),
        }
        if delta == 0:
            matches.append(item)
        else:
            mismatches.append(item)

    return {
        "summary": {
            "pycefr_entries": len(pycefr_records),
            "radon_entries": len(radon_records),
            "only_pycefr": len(only_pycefr),
            "only_radon": len(only_radon),
            "mismatches": len(mismatches),
            "matches": len(matches),
        },
        "only_pycefr": only_pycefr,
        "only_radon": only_radon,
        "mismatches": mismatches,
        "matches": matches,
    }


def print_report(report: dict[str, Any], show_matches: bool) -> None:
    summary = report["summary"]
    print("=== Comparison Summary ===")
    print(f"PyCEFR entries:      {summary['pycefr_entries']}")
    print(f"radon entries:       {summary['radon_entries']}")
    print(f"Only in PyCEFR:      {summary['only_pycefr']}")
    print(f"Only in radon:       {summary['only_radon']}")
    print(f"Mismatched CC values:{summary['mismatches']}")
    print(f"Matching CC values:  {summary['matches']}")

    if report["mismatches"]:
        print("\n=== Mismatches (PyCEFR vs radon) ===")
        for item in report["mismatches"]:
            key = item["key"]
            print(
                f"- {key['file']}::{key['name']} (line={key['line']}, type={key['type']}) "
                f"=> {item['pycefr_complexity']} vs {item['radon_complexity']} "
                f"(delta={item['delta']:+.2f})"
            )

    if report["only_pycefr"]:
        print("\n=== Only in PyCEFR ===")
        for item in report["only_pycefr"]:
            print(
                f"- {item['file']}::{item['name']} (line={item['line']}, type={item['type']}) "
                f"cc={item['complexity']}"
            )

    if report["only_radon"]:
        print("\n=== Only in radon ===")
        for item in report["only_radon"]:
            print(
                f"- {item['file']}::{item['name']} (line={item['line']}, type={item['type']}) "
                f"cc={item['complexity']}"
            )

    if show_matches and report["matches"]:
        print("\n=== Matches ===")
        for item in report["matches"]:
            key = item["key"]
            print(
                f"- {key['file']}::{key['name']} (line={key['line']}, type={key['type']}) "
                f"cc={item['pycefr_complexity']}"
            )


def main() -> int:
    args = parse_args()
    run_id = f"run-{int(time.time() * 1000)}"

    # region agent log
    debug_log(
        run_id=run_id,
        hypothesis_id="H1",
        location="src/generator.py:main:args",
        message="CLI arguments received",
        data={
            "cwd": os.getcwd(),
            "pycefr": args.pycefr,
            "radon": args.radon,
            "output": args.output,
            "show_matches": args.show_matches,
        },
    )
    # endregion

    pycefr_data = read_json(args.pycefr)
    radon_data = read_json(args.radon)

    pycefr_records = extract_records(pycefr_data, "pycefr")
    radon_records = extract_records(radon_data, "radon")
    report = compare(pycefr_records, radon_records)

    print_report(report, show_matches=args.show_matches)

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("w", encoding="utf-8") as handle:
            json.dump(report, handle, indent=2, ensure_ascii=False)
        print(f"\nReport written to: {output_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())