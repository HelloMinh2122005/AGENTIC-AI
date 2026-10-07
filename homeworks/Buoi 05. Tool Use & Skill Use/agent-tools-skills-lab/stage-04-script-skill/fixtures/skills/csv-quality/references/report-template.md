# Báo cáo phân tích công việc và chất lượng dữ liệu: `{đường dẫn CSV}`

Công cụ: `skills/csv-quality/scripts/check_csv.py` | exit code: {exit_code} | Ngưỡng giờ: {max_hours} giờ

## Tổng quan
| Chỉ số | Giá trị |
|---|---|
| Số dòng dữ liệu (không tính header) | {row_count} |
| Ngưỡng giờ tối đa (`max_hours`) | {max_hours} |
| Dòng thiếu owner | {missing_owner_count} |
| Dòng hours không hợp lệ | {invalid_hours_count} |
| Số task_id bị lặp (distinct) | {duplicate_id_count} ({duplicate_ids}) |
| Tổng số dòng bị loại khỏi tính giờ | {len(excluded_rows)} |

## Tổng giờ theo nhân sự
| Nhân sự (Owner) | Tổng giờ hợp lệ | Tình trạng |
|---|---|---|
| {owner} | {total_hours} | {Quá tải / Trong định mức} |

## Danh sách nhân sự quá tải
- {Danh sách nhân sự có tổng giờ > max_hours; nếu không có ai ghi: "Không có nhân sự nào vượt ngưỡng"}

## Chi tiết các dòng bị loại
| Dòng (Line) | task_id | Các mã lý do loại |
|---|---|---|
| {line} | {task_id} | {reasons} |

## Chi tiết lỗi dữ liệu
| Line | Cột | Loại | task_id | Mô tả |
|---|---|---|---|---|
| {line} | {column} | {type} | {task_id} | {message} |

## Đánh giá
- Tình hình quá tải công việc theo ngưỡng {max_hours} giờ.
- Mức độ tin cậy của dữ liệu dựa trên các dòng bị loại.

## Khuyến nghị
- Đề xuất phân bổ lại công việc cho nhân sự vượt ngưỡng.
- Đề xuất làm sạch dữ liệu nguồn đối với các dòng bị loại (không tự ý sửa file CSV gốc).
