#!/usr/bin/env python3
"""Kiểm tra chất lượng CSV công việc (task_id, owner, hours) và tính tổng giờ/quá tải.

Cách chạy (cwd là workspace):
    python skills/csv-quality/scripts/check_csv.py --input data/workload.csv --max-hours 8

Exit 0: phân tích thành công, kể cả khi dữ liệu có lỗi chất lượng hoặc người quá tải.
Exit 1: file không tồn tại/không đọc được, thiếu cột bắt buộc, lỗi parse CSV hoặc tham số --max-hours không hợp lệ; thông báo ra stderr.
Exit 2: thiếu tham số bắt buộc CLI (argparse).
Script chỉ đọc, không sửa CSV đầu vào.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import sys

REQUIRED_COLUMNS = ("task_id", "owner", "hours")


class InputError(Exception):
    pass


def parse_hours(raw: str | None) -> float | None:
    """Số giờ hợp lệ: số hữu hạn, không âm. Trả None nếu không hợp lệ."""
    if raw is None or not raw.strip():
        return None
    try:
        value = float(raw.strip())
    except ValueError:
        return None
    if not math.isfinite(value) or value < 0:
        return None
    return value


def clean_num(val: float) -> int | float:
    """Chuyển đổi số float thành int nếu là số nguyên để JSON gọn gàng."""
    return int(val) if isinstance(val, (int, float)) and float(val).is_integer() else round(val, 4)


def analyze(path: str, max_hours: float) -> dict:
    try:
        handle = open(path, encoding="utf-8-sig", newline="")
    except OSError as exc:
        raise InputError(f"Không đọc được file {path}: {exc.strerror or exc}") from exc
    with handle:
        reader = csv.reader(handle, strict=True)
        try:
            header = next(reader, None)
            if header is None:
                raise InputError(f"File {path} rỗng, không có header.")
            columns = [c.strip() for c in header]
            missing = [c for c in REQUIRED_COLUMNS if c not in columns]
            if missing:
                raise InputError(f"Thiếu cột bắt buộc: {', '.join(missing)}. Header hiện có: {', '.join(columns)}")
            index = {name: columns.index(name) for name in REQUIRED_COLUMNS}

            row_count = 0
            missing_owner = 0
            invalid_hours = 0
            first_seen: dict[str, int] = {}
            duplicate_ids: list[str] = []
            issues: list[dict] = []

            # Thống kê tính giờ và dòng bị loại
            raw_hours_by_owner: dict[str, float] = {}
            valid_owners: set[str] = set()
            excluded_rows: list[dict] = []

            for row in reader:
                line = reader.line_num
                if not any(cell.strip() for cell in row):
                    continue  # bỏ qua dòng trống
                row_count += 1

                def cell(name: str) -> str:
                    position = index[name]
                    return row[position].strip() if position < len(row) else ""

                task_id, owner, hours = cell("task_id"), cell("owner"), cell("hours")

                # Danh sách lý do loại dòng sắp xếp theo đúng thứ tự hợp đồng:
                # 1. wrong_field_count
                # 2. missing_task_id
                # 3. duplicate_id
                # 4. missing_owner
                # 5. invalid_hours
                reasons: list[str] = []

                if len(row) != len(columns):
                    reasons.append("wrong_field_count")
                    issues.append({"line": line, "column": None, "type": "wrong_field_count", "task_id": task_id or None,
                                   "message": f"Có {len(row)} trường, header có {len(columns)} cột."})

                if not task_id:
                    reasons.append("missing_task_id")
                    issues.append({"line": line, "column": "task_id", "type": "missing_task_id", "task_id": None,
                                   "message": "task_id trống."})
                elif task_id in first_seen:
                    if task_id not in duplicate_ids:
                        duplicate_ids.append(task_id)
                    reasons.append("duplicate_id")
                    issues.append({"line": line, "column": "task_id", "type": "duplicate_id", "task_id": task_id,
                                   "message": f"task_id {task_id} đã xuất hiện ở line {first_seen[task_id]}."})
                else:
                    first_seen[task_id] = line

                if not owner:
                    missing_owner += 1
                    reasons.append("missing_owner")
                    issues.append({"line": line, "column": "owner", "type": "missing_owner", "task_id": task_id or None,
                                   "message": "owner trống."})

                parsed_h = parse_hours(hours)
                if parsed_h is None:
                    invalid_hours += 1
                    reasons.append("invalid_hours")
                    issues.append({"line": line, "column": "hours", "type": "invalid_hours", "task_id": task_id or None,
                                   "value": hours, "message": f"hours '{hours}' không phải số hữu hạn không âm."})

                if reasons:
                    excluded_rows.append({
                        "line": line,
                        "task_id": task_id if task_id else None,
                        "reasons": reasons,
                    })
                else:
                    raw_hours_by_owner[owner] = raw_hours_by_owner.get(owner, 0.0) + parsed_h
                    valid_owners.add(owner)

        except csv.Error as exc:
            raise InputError(f"Lỗi parse CSV ở line {reader.line_num}: {exc}") from exc
        except UnicodeDecodeError as exc:
            raise InputError(f"File {path} không phải UTF-8: {exc}") from exc

    # Chỉ đưa vào hours_by_owner những owner có ít nhất một dòng được cộng
    hours_by_owner = {
        owner: clean_num(raw_hours_by_owner[owner])
        for owner in raw_hours_by_owner
        if owner in valid_owners
    }

    # Người quá tải: total_hours > max_hours, sắp xếp theo tên owner
    overloaded_owners = []
    for owner in sorted(hours_by_owner.keys()):
        total = raw_hours_by_owner[owner]
        if total > max_hours:
            overloaded_owners.append({
                "owner": owner,
                "total_hours": clean_num(total)
            })

    return {
        "input": path,
        "row_count": row_count,
        "missing_owner_count": missing_owner,
        "invalid_hours_count": invalid_hours,
        "duplicate_id_count": len(duplicate_ids),
        "duplicate_ids": duplicate_ids,
        "issues": sorted(issues, key=lambda item: item["line"]),
        "max_hours": clean_num(max_hours),
        "hours_by_owner": hours_by_owner,
        "overloaded_owners": overloaded_owners,
        "excluded_rows": sorted(excluded_rows, key=lambda item: item["line"]),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Kiểm tra chất lượng CSV công việc và phát hiện người quá tải.")
    parser.add_argument("--input", required=True, help="Đường dẫn CSV, ví dụ data/workload.csv")
    parser.add_argument("--max-hours", required=True, help="Ngưỡng giờ tối đa cho phép (số hữu hạn không âm)")
    args = parser.parse_args(argv)

    try:
        max_h = float(args.max_hours)
        if not math.isfinite(max_h) or max_h < 0:
            raise ValueError()
    except (ValueError, TypeError):
        print(f"ERROR: Tham số --max-hours phải là số hữu hạn không âm, nhận được: '{args.max_hours}'", file=sys.stderr)
        return 1

    try:
        result = analyze(args.input, max_h)
    except InputError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
