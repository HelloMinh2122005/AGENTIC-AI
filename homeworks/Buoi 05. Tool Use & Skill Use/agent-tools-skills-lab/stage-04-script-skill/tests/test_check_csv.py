"""csv-quality script: thống kê fixture, lỗi input/schema/parse exit 1, lỗi dữ liệu exit 0, tính tổng giờ và phát hiện quá tải."""

import json
import subprocess
import sys

import pytest

import paths

SCRIPT = paths.FIXTURES_DIR / "skills" / "csv-quality" / "scripts" / "check_csv.py"


def run(path, max_hours: float | str | None = 8):
    cmd = [sys.executable, str(SCRIPT), "--input", str(path)]
    if max_hours is not None:
        cmd.extend(["--max-hours", str(max_hours)])
    return subprocess.run(cmd, capture_output=True, text=True, timeout=10)


def write_csv(tmp_path, text):
    path = tmp_path / "t.csv"
    path.write_text(text, encoding="utf-8")
    return path


def test_fixture_statistics():
    result = run(paths.FIXTURES_DIR / "data" / "tasks.csv", max_hours=8)
    assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout)
    assert data["row_count"] == 6
    assert data["missing_owner_count"] == 1
    assert data["invalid_hours_count"] == 1
    assert data["duplicate_id_count"] == 1
    assert data["duplicate_ids"] == ["T02"]
    assert [(i["line"], i["column"], i["type"]) for i in data["issues"]] == [
        (4, "owner", "missing_owner"),
        (5, "hours", "invalid_hours"),
        (6, "task_id", "duplicate_id"),
    ]
    assert data["max_hours"] == 8
    assert "hours_by_owner" in data
    assert "excluded_rows" in data
    assert "total_hours" not in data


@pytest.mark.parametrize("hours", ["NaN", "nan", "Infinity", "-inf", "-1", ""])
def test_non_finite_negative_or_empty_hours_rejected(tmp_path, hours):
    data = json.loads(run(write_csv(tmp_path, f"task_id,owner,hours\nT01,Lan,{hours}\n"), max_hours=8).stdout)
    assert data["invalid_hours_count"] == 1
    assert data["issues"][0]["line"] == 2


def test_clean_data_exit_0_without_issues(tmp_path):
    result = run(write_csv(tmp_path, "task_id,owner,hours\nT01,Lan,4\nT02,Minh,2.5\n"), max_hours=8)
    assert result.returncode == 0
    assert json.loads(result.stdout)["issues"] == []
    assert json.loads(result.stdout)["hours_by_owner"] == {"Lan": 4, "Minh": 2.5}


def test_missing_file_exit_1(tmp_path):
    result = run(tmp_path / "khong-co.csv", max_hours=8)
    assert result.returncode == 1
    assert result.stdout == ""
    assert "Không đọc được file" in result.stderr


def test_missing_column_exit_1(tmp_path):
    result = run(write_csv(tmp_path, "task_id,owner\nT01,Lan\n"), max_hours=8)
    assert result.returncode == 1
    assert "Thiếu cột bắt buộc: hours" in result.stderr


def test_parse_error_exit_1(tmp_path):
    result = run(write_csv(tmp_path, 'task_id,owner,hours\nT01,"La"n,4\n'), max_hours=8)
    assert result.returncode == 1
    assert "Lỗi parse CSV" in result.stderr


def test_script_does_not_modify_input():
    source = paths.FIXTURES_DIR / "data" / "tasks.csv"
    before = source.read_bytes()
    run(source, max_hours=8)
    assert source.read_bytes() == before


def test_missing_or_invalid_max_hours():
    # Thiếu --max-hours
    res_missing = run(paths.FIXTURES_DIR / "data" / "tasks.csv", max_hours=None)
    assert res_missing.returncode != 0
    assert "required: --max-hours" in res_missing.stderr or "the following arguments are required" in res_missing.stderr

    # --max-hours âm
    res_neg = run(paths.FIXTURES_DIR / "data" / "tasks.csv", max_hours=-1)
    assert res_neg.returncode == 1
    assert "ERROR: Tham số --max-hours phải là số hữu hạn không âm" in res_neg.stderr

    # --max-hours không phải số
    res_str = run(paths.FIXTURES_DIR / "data" / "tasks.csv", max_hours="abc")
    assert res_str.returncode == 1
    assert "ERROR: Tham số --max-hours phải là số hữu hạn không âm" in res_str.stderr


def test_workload_analysis_threshold_8_and_9(tmp_path):
    csv_text = """task_id,owner,hours
T01,Lan,4
T02,Lan,5
T03,Minh,3
T04,Minh,abc
T02,Lan,5
T05,,2
"""
    p = write_csv(tmp_path, csv_text)

    # Ngưỡng 8
    res8 = run(p, max_hours=8)
    assert res8.returncode == 0
    d8 = json.loads(res8.stdout)
    assert d8["hours_by_owner"] == {"Lan": 9, "Minh": 3}
    assert d8["overloaded_owners"] == [{"owner": "Lan", "total_hours": 9}]
    assert [x["line"] for x in d8["excluded_rows"]] == [5, 6, 7]
    assert d8["excluded_rows"][0]["reasons"] == ["invalid_hours"]
    assert d8["excluded_rows"][1]["reasons"] == ["duplicate_id"]
    assert d8["excluded_rows"][2]["reasons"] == ["missing_owner"]

    # Ngưỡng 9
    res9 = run(p, max_hours=9)
    assert res9.returncode == 0
    d9 = json.loads(res9.stdout)
    assert d9["hours_by_owner"] == {"Lan": 9, "Minh": 3}
    assert d9["overloaded_owners"] == []


def test_edge_case_first_seen_invalid_hours_not_credited(tmp_path):
    csv_text = """task_id,owner,hours
E01,Lan,abc
E01,Lan,5
E02,Minh,0
"""
    p = write_csv(tmp_path, csv_text)
    res = run(p, max_hours=0)
    assert res.returncode == 0
    d = json.loads(res.stdout)
    assert d["hours_by_owner"] == {"Minh": 0}
    assert d["overloaded_owners"] == []
    assert len(d["excluded_rows"]) == 2
    assert d["excluded_rows"][0] == {"line": 2, "task_id": "E01", "reasons": ["invalid_hours"]}
    assert d["excluded_rows"][1] == {"line": 3, "task_id": "E01", "reasons": ["duplicate_id"]}
