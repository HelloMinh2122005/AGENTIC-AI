# BTVN Buổi 05: Tool Use & Skill Use (Agentic AI Engineering)

**Học viên:** Phan Đình Minh (MSSV: 23520949)  
**Lớp / Môn học:** SE373 - Kỹ nghệ Hệ thống Agentic AI  
**Repository GitHub:** [HelloMinh2122005/AGENTIC-AI](https://github.com/HelloMinh2122005/AGENTIC-AI)  
**Thư mục bài tập:** [`homeworks/Buoi 05. Tool Use & Skill Use`](https://github.com/HelloMinh2122005/AGENTIC-AI/tree/main/homeworks/Buoi%2005.%20Tool%20Use%20%26%20Skill%20Use)

---

## Cấu trúc thư mục nộp bài

```text
Buoi 05. Tool Use & Skill Use/
├── link-github.txt                                 # Link dẫn đến folder bài nộp trên GitHub
├── link-git.txt                                    # Bản phụ link repo
├── README.md                                       # Báo cáo tổng hợp toàn bộ bài làm
└── agent-tools-skills-lab/                         # Toàn bộ mã nguồn lab 5 stages
    ├── stage-00-chat/                              # Stage 0: Chat cơ bản (xác định giới hạn agent)
    ├── stage-01-files/                             # Stage 1: Thêm tool file, triển khai list_files
    │   ├── tools/files.py                          # Cài đặt list_files, read_file, write_file
    │   └── tests/test_files.py                     # Unit tests cho file tools
    ├── stage-02-skills/                            # Stage 2: Tích hợp tool list_files và skill refund-policy
    │   ├── workspace/data/policies/                # 2 file markdown chính sách hoàn tiền
    │   │   ├── policy-before-oct.md                # Chính sách trước tháng 10
    │   │   └── policy-from-oct.md                  # Chính sách từ tháng 10
    │   ├── workspace/skills/refund-policy/         # Thư mục skill refund-policy
    │   │   ├── SKILL.md                            # Hướng dẫn tra cứu & chọn chính sách
    │   │   └── references/answer-template.md       # Mẫu câu trả lời
    │   ├── traces/                                 # File JSONL trace cho các trường hợp A, B, thiếu thông tin
    │   └── analysis.md                             # Báo cáo phân tích và trả lời câu hỏi Block 1
    ├── stage-03-bash/                              # Stage 3: Chạy Bash, đối chiếu số giờ với workload.csv
    │   └── workspace/data/workload.csv             # Dữ liệu công việc kiểm tra
    └── stage-04-script-skill/                      # Stage 4: Mở rộng check_csv.py và cập nhật skill csv-quality
        ├── workspace/skills/csv-quality/
        │   ├── scripts/check_csv.py                # Script nâng cấp CLI --max-hours, lọc trùng ID, tính tổng giờ
        │   ├── SKILL.md                            # Skill cập nhật nhận ngưỡng giờ
        │   └── references/report-template.md       # Template báo cáo chi tiết
        ├── workspace/data/
        │   ├── workload.csv                        # File test chính
        │   └── workload-edge.csv                   # Edge case: ID đầu tiên có hours lỗi
        ├── workspace/output/workload.md            # Báo cáo Markdown agent tạo
        ├── traces/                                 # File JSONL trace cho ngưỡng 8, 9, thiếu ngưỡng, file thiếu
        ├── tests/test_check_csv.py                 # Unit tests tự động cho script và edge case
        └── analysis.md                             # Báo cáo phân tích và trả lời câu hỏi Block 2
```

---

## Tóm tắt kết quả 2 Block bài tập

### 1. Block 1: Tra cứu chính sách đúng phiên bản
- Đã cài đặt hoàn chỉnh tool `list_files(path: str)` trong `tools/files.py` ở cả stage 01 và stage 02. Tool bảo vệ an toàn workspace, chặn traversal/escape, báo lỗi rõ ràng nếu đường dẫn là file hoặc không tồn tại.
- Đã tạo 2 tài liệu chính sách `policy-before-oct.md` và `policy-from-oct.md`.
- Đã tạo skill `refund-policy` (`SKILL.md` và `answer-template.md`).
- Đã ghi nhận trace cho 3 trường hợp:
  1. **Trường hợp A:** Mua 28/09/2026, hoàn 06/10/2026 $\rightarrow$ Quá hạn 8 ngày $\rightarrow$ Không đủ điều kiện.
  2. **Trường hợp B (sau khi đổi tên file chính sách):** Mua 02/10/2026, hoàn 12/10/2026 $\rightarrow$ 10 ngày $\le$ 14 ngày $\rightarrow$ Đủ điều kiện, 0 đồng phí. Agent dùng `list_files` phát hiện tên file mới mà không phụ thuộc vào tên cũ.
  3. **Trường hợp C (Thiếu thông tin):** Mua 02/10/2026, hoàn 12/10/2026 $\rightarrow$ Agent hỏi lại trạng thái kích hoạt, không tự giả định.
- Báo cáo chi tiết và giải thích lý thuyết nằm tại [`stage-02-skills/analysis.md`](agent-tools-skills-lab/stage-02-skills/analysis.md).

### 2. Block 2: Kiểm tra quá tải theo người
- Đã nâng cấp script `check_csv.py` với tham số bắt buộc `--max-hours`, chuẩn hóa strip whitespace, quy tắc deduplicate ID chỉ giữ lần xuất hiện đầu tiên trong file, tính tổng giờ theo người và xác định danh sách quá tải.
- Đã cập nhật `SKILL.md` và `references/report-template.md`, đồng bộ đầy đủ sang `fixtures/`.
- Đã tạo `workload-edge.csv` và viết test tự động `test_edge_case_first_seen_invalid_hours_not_credited` trong `tests/test_check_csv.py`.
- Kết quả chạy trực tiếp:
  - Ngưỡng 8: Lan 9 giờ (quá tải), Minh 3 giờ. Dòng 5, 6, 7 bị loại.
  - Ngưỡng 9: Lan 9 giờ, Minh 3 giờ. Không ai quá tải.
  - Ngưỡng 0 (edge case): Lan không được tính 5 giờ (dòng 2 lỗi invalid, dòng 3 duplicate), chỉ Minh 0 giờ.
- Đã ghi nhận trace cho 4 trường hợp: Ngưỡng 8, Ngưỡng 9, Thiếu ngưỡng (Agent hỏi lại), và File không tồn tại (Agent báo lỗi stderr).
- Báo cáo chi tiết và giải thích lý thuyết nằm tại [`stage-04-script-skill/analysis.md`](agent-tools-skills-lab/stage-04-script-skill/analysis.md).

### 3. Trạng thái kiểm thử tự động
Toàn bộ **214/214 tests** trên cả 5 stages đều đạt kết quả PASS:
- `stage-00-chat`: 17 passed
- `stage-01-files`: 39 passed
- `stage-02-skills`: 46 passed
- `stage-03-bash`: 48 passed
- `stage-04-script-skill`: 64 passed
