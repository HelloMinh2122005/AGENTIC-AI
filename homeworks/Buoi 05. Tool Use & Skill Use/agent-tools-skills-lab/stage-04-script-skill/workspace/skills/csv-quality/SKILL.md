---
name: csv-quality
description: Kiểm tra chất lượng file CSV danh sách công việc (cột task_id, owner, hours), tính tổng giờ theo người và xác định người quá tải theo ngưỡng giờ bằng script có sẵn, rồi ghi báo cáo Markdown dưới output/. Dùng khi người dùng yêu cầu kiểm tra, rà soát chất lượng CSV công việc, tính tổng giờ hoặc kiểm tra quá tải nhân sự.
---

# CSV quality & Workload Analysis

Kiểm tra chất lượng CSV công việc, tính tổng giờ hợp lệ theo nhân sự và phát hiện quá tải bằng script có sẵn.

## Quy tắc nhận ngưỡng giờ

- Phân tích quá tải bắt buộc phải có ngưỡng giờ tối đa (`--max-hours`).
- **Nếu người dùng chưa cung cấp ngưỡng giờ:** Phải hỏi lại người dùng để nhận ngưỡng giờ trước khi chạy script hoặc kết luận. Tuyệt đối không tự bịa ngưỡng (ví dụ tự gán 8) và không dùng ngưỡng từ các cuộc trò chuyện trước.
- Ngưỡng giờ phải là số hữu hạn không âm.

## Chạy script

Dùng tool `bash` (cwd là workspace). Lệnh đầy đủ:

```
python skills/csv-quality/scripts/check_csv.py --input <đường dẫn CSV> --max-hours <ngưỡng giờ>
```

Ví dụ: `python skills/csv-quality/scripts/check_csv.py --input data/workload.csv --max-hours 8`

Không cần đọc source script để chạy. Chỉ đọc `scripts/check_csv.py` khi cần hiểu một hành vi mà phần dưới không mô tả.

## Kiểm tra kết quả

- `exit_code` 0: phân tích thành công. `stdout` là JSON gồm các trường:
  - Thống kê chất lượng: `row_count`, `missing_owner_count`, `invalid_hours_count`, `duplicate_id_count`, `duplicate_ids`, `issues`.
  - Thống kê công việc: `max_hours`, `hours_by_owner` (tổng giờ theo từng người có dòng hợp lệ), `overloaded_owners` (danh sách người có tổng giờ vượt ngưỡng), `excluded_rows` (danh sách các dòng bị loại kèm mã lý do).
- `exit_code` khác 0: **lỗi thực thi** (file không tồn tại, thiếu cột bắt buộc, lỗi cú pháp CSV hoặc sai tham số CLI). Đọc `stderr`, báo lỗi cho người dùng. Không bịa thống kê, không ghi báo cáo như thể đã phân tích thành công.
- `timed_out` true hoặc `ok` false: lệnh không chạy xong; báo lỗi, không suy đoán kết quả.
- Phân biệt rõ **lỗi dữ liệu** (nằm trong `issues` / `excluded_rows`, script vẫn chạy thành công) với **lỗi thực thi** (exit khác 0).

## Viết báo cáo

1. Đọc template `references/report-template.md` trong thư mục skill này, tức `skills/csv-quality/references/report-template.md`.
2. Lấy mọi con số từ JSON của script. Điền đầy đủ:
   - Ngưỡng giờ áp dụng (`max_hours`).
   - Bảng tổng giờ theo người (`hours_by_owner`).
   - Danh sách người bị quá tải (`overloaded_owners`).
   - Bảng chi tiết các dòng bị loại (`excluded_rows`) kèm thứ tự các mã lý do.
   - Chi tiết các vấn đề chất lượng dữ liệu (`issues`).
3. Không sửa file CSV nguồn.
4. Ghi báo cáo bằng `write_file` vào đường dẫn người dùng yêu cầu (ví dụ `output/workload.md` hoặc `output/csv-quality.md`), rồi trả lời tóm tắt ngắn gọn.
