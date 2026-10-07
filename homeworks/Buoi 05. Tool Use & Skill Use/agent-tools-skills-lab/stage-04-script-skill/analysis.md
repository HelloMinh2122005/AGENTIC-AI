# Báo cáo phân tích Block 2: Kiểm tra quá tải theo người

**Học phần:** Agentic AI Engineering (D05 - Tool Use & Skill Use)  
**Nhóm sinh viên:** Phan Đình Minh (MSSV: 23520949)  
**Project:** `stage-04-script-skill` (kế thừa từ `stage-03-bash`)

---

## 1. Các thay đổi đã thực hiện

1. **Mở rộng script [`check_csv.py`](file:///home/phandinhminh/Downloads/AGENTIC-AI/homeworks/Buoi%2005.%20Tool%20Use%20&%20Skill%20Use/agent-tools-skills-lab/stage-04-script-skill/workspace/skills/csv-quality/scripts/check_csv.py):**
   - Thêm tham số CLI bắt buộc `--max-hours` (số hữu hạn $\ge 0$). Nếu thiếu hoặc âm $\rightarrow$ in lỗi ra stderr, exit code 1 hoặc 2.
   - Chuẩn hóa: strip khoảng trắng đầu/cuối ở `task_id`, `owner`, `hours`. Phân biệt chữ hoa/thường theo owner.
   - **Quy tắc deduplicate ID:** Chỉ giữ lần xuất hiện đầu tiên của mỗi `task_id` trong file. Mọi lần xuất hiện sau đều bị đánh dấu `duplicate_id` và bị loại, kể cả khi lần đầu chứa dữ liệu lỗi.
   - **Tiêu chí cộng giờ:** Chỉ cộng giờ khi dòng thỏa mãn: đúng số trường, `task_id` không rỗng và chưa từng xuất hiện, `owner` không rỗng, và `hours` là số hữu hạn $\ge 0$.
   - **Bổ sung đầu ra JSON:**
     - `max_hours`: ngưỡng giờ nhận từ CLI.
     - `hours_by_owner`: map `{owner: total_hours}` (chỉ chứa owner có ít nhất 1 dòng hợp lệ).
     - `overloaded_owners`: danh sách `[{"owner": ..., "total_hours": ...}]` cho người có `total_hours > max_hours`.
     - `excluded_rows`: danh sách các dòng bị loại kèm mã lý do được sắp xếp chuẩn: `wrong_field_count`, `missing_task_id`, `duplicate_id`, `missing_owner`, `invalid_hours`.
2. **Cập nhật Skill [`SKILL.md`](file:///home/phandinhminh/Downloads/AGENTIC-AI/homeworks/Buoi%2005.%20Tool%20Use%20&%20Skill%20Use/agent-tools-skills-lab/stage-04-script-skill/workspace/skills/csv-quality/SKILL.md):**
   - Hướng dẫn gọi script với tham số `--max-hours <ngưỡng>`.
   - Quy định rõ: **Nếu người dùng chưa cung cấp ngưỡng giờ, Agent bắt buộc phải hỏi lại**, không tự ý gán giá trị mặc định hay lấy từ phiên chat cũ.
3. **Cập nhật Reference [`report-template.md`](file:///home/phandinhminh/Downloads/AGENTIC-AI/homeworks/Buoi%2005.%20Tool%20Use%20&%20Skill%20Use/agent-tools-skills-lab/stage-04-script-skill/workspace/skills/csv-quality/references/report-template.md):**
   - Bổ sung bảng tổng giờ theo nhân sự, danh sách nhân sự quá tải và danh sách các dòng bị loại kèm mã lý do.
4. **Đồng bộ hóa Fixtures:**
   - Đã sao chép toàn bộ skill đã cập nhật sang `fixtures/skills/csv-quality/` và dữ liệu sang `fixtures/data/`.
5. **Kiểm thử tự động:**
   - Bổ sung unit tests trong `tests/test_check_csv.py` kiểm tra: tham số `--max-hours` thiếu/âm, phân tích ngưỡng 8 và 9, và edge case lần đầu của ID có hours không hợp lệ.

---

## 2. Kết quả chạy trực tiếp Script CLI & JSON Output

### 2.1. Với dữ liệu `data/workload.csv` và ngưỡng 8 (`--max-hours 8`):
Lệnh chạy:
```bash
uv run python workspace/skills/csv-quality/scripts/check_csv.py --input workspace/data/workload.csv --max-hours 8
```
Output JSON:
```json
{
  "input": "workspace/data/workload.csv",
  "row_count": 6,
  "missing_owner_count": 1,
  "invalid_hours_count": 1,
  "duplicate_id_count": 1,
  "duplicate_ids": ["T02"],
  "issues": [
    {"line": 5, "column": "hours", "type": "invalid_hours", "task_id": "T04", "value": "abc", "message": "hours 'abc' không phải số hữu hạn không âm."},
    {"line": 6, "column": "task_id", "type": "duplicate_id", "task_id": "T02", "message": "task_id T02 đã xuất hiện ở line 3."},
    {"line": 7, "column": "owner", "type": "missing_owner", "task_id": "T05", "message": "owner trống."}
  ],
  "max_hours": 8,
  "hours_by_owner": {
    "Lan": 9,
    "Minh": 3
  },
  "overloaded_owners": [
    {"owner": "Lan", "total_hours": 9}
  ],
  "excluded_rows": [
    {"line": 5, "task_id": "T04", "reasons": ["invalid_hours"]},
    {"line": 6, "task_id": "T02", "reasons": ["duplicate_id"]},
    {"line": 7, "task_id": "T05", "reasons": ["missing_owner"]}
  ]
}
```
*Nhận xét:* Lan có tổng 9 giờ (> 8 giờ $\rightarrow$ Quá tải). Minh có 3 giờ ($\le 8$ giờ $\rightarrow$ Không quá tải). Các dòng 5, 6, 7 bị loại chính xác.

### 2.2. Với cùng dữ liệu và ngưỡng 9 (`--max-hours 9`):
Lệnh chạy:
```bash
uv run python workspace/skills/csv-quality/scripts/check_csv.py --input workspace/data/workload.csv --max-hours 9
```
*Kết quả:*
- `hours_by_owner`: `{"Lan": 9, "Minh": 3}`
- `overloaded_owners`: `[]` (Không có ai bị quá tải vì Lan = 9, bằng ngưỡng nên không quá tải).
- `excluded_rows`: Giữ nguyên dòng 5, 6, 7.

### 2.3. Trường hợp đặc biệt (Edge Case): `data/workload-edge.csv` với ngưỡng 0:
File đầu vào:
```csv
task_id,owner,hours
E01,Lan,abc
E01,Lan,5
E02,Minh,0
```
Lệnh chạy:
```bash
uv run python workspace/skills/csv-quality/scripts/check_csv.py --input workspace/data/workload-edge.csv --max-hours 0
```
*Kết quả JSON:*
```json
{
  "max_hours": 0,
  "hours_by_owner": {
    "Minh": 0
  },
  "overloaded_owners": [],
  "excluded_rows": [
    {"line": 2, "task_id": "E01", "reasons": ["invalid_hours"]},
    {"line": 3, "task_id": "E01", "reasons": ["duplicate_id"]}
  ]
}
```
*Đánh giá:* Dòng 2 (`E01`, Lan) bị loại do `invalid_hours`. Dòng 3 (`E01`, Lan) bị loại do `duplicate_id`. Lan không được cộng 5 giờ. Chỉ Minh có 0 giờ. Không ai quá tải. Test tự động `test_edge_case_first_seen_invalid_hours_not_credited` passed 100%.

---

## 3. Kết quả các trường hợp chạy Agent & Vị trí bằng chứng trong Trace

Các trace được lưu tại thư mục `traces/`:

### 3.1. Ngưỡng 8: "Kiểm tra data/workload.csv, người nào vượt 8 giờ? Ghi báo cáo vào output/workload.md."
- **File trace:** `traces/20261007-222244_61018c1f_turn01_ec48a0f5.jsonl`
- **File báo cáo sinh ra:** `workspace/output/workload.md`
- **Bằng chứng trong trace:**
  - Dòng 3-5: Gọi `read_file("skills/csv-quality/SKILL.md")`.
  - Dòng 7-10: Gọi song song `bash("python skills/csv-quality/scripts/check_csv.py --input data/workload.csv --max-hours 8")` và `read_file("skills/csv-quality/references/report-template.md")`.
  - Dòng 12-14: Gọi `write_file("output/workload.md", ...)` ghi nội dung báo cáo đầy đủ bảng giờ, người quá tải và các dòng bị loại.
  - Dòng 15: Trả lời tóm tắt cho người dùng: Lan 9 giờ (quá tải), Minh 3 giờ.

### 3.2. Ngưỡng 9: "Kiểm tra data/workload.csv, người nào vượt 9 giờ? Ghi báo cáo vào output/workload.md."
- **File trace:** `traces/20261007-222244_9053c2d2_turn01_593769d1.jsonl`
- **Bằng chứng trong trace:**
  - Dòng 7-10: Gọi bash với `--max-hours 9`.
  - Dòng 15: Trả lời rõ: Không có nhân sự nào vượt ngưỡng 9 giờ.

### 3.3. Thiếu ngưỡng: "Tính tổng giờ theo người trong data/workload.csv và xác định người quá tải."
- **File trace:** `traces/20261007-222244_7df920e0_turn01_fd0c989a.jsonl`
- **Bằng chứng trong trace:**
  - Dòng 3-5: Đọc `SKILL.md`.
  - Dòng 7: Model dừng gọi tool và hỏi lại người dùng để lấy ngưỡng giờ trước khi chạy script.

### 3.4. File không tồn tại: "Kiểm tra data/khong-ton-tai.csv, người nào vượt 8 giờ? Ghi báo cáo vào output/workload.md."
- **File trace:** `traces/20261007-222244_6d612610_turn01_e15c6f59.jsonl`
- **Bằng chứng trong trace:**
  - Dòng 7-10: Gọi bash $\rightarrow$ Nhận exit code 1, stderr báo lỗi file không tồn tại.
  - Dòng 11: Model báo lỗi thực thi ra ngoài màn hình chat, không bịa đặt số liệu hay cố tình ghi báo cáo rỗng.

---

## 4. Trả lời câu hỏi cuối bài (Block 2)

### Câu hỏi:
> *Phần nào do script tính, phần nào do model diễn giải? Nếu sửa script nhưng không cập nhật skill và reference, báo cáo có thể sai hoặc thiếu thông tin gì?*

### Trả lời:
1. **Phần nào do script tính?**
   - Đọc, parse và kiểm tra cú pháp file CSV (kiểm tra encoding, header, số cột).
   - Xác định và phân loại các lỗi dữ liệu (`missing_task_id`, `duplicate_id`, `missing_owner`, `invalid_hours`).
   - Lọc deduplicate: xác định lần xuất hiện đầu tiên của `task_id` và đánh dấu các lần sau là dòng bị loại.
   - Tính toán số học: tổng giờ hợp lệ cho từng nhân sự (`hours_by_owner`).
   - So sánh ngưỡng định lượng: xác định danh sách người vượt ngưỡng (`overloaded_owners`).
   - **Tóm lại:** Toàn bộ phần tính toán số học, logic xác định hợp lệ và so sánh ngưỡng được thực hiện hoàn toàn bởi **mã nguồn Python tất định (deterministic execution)** trong script, đảm bảo độ chính xác tuyệt đối, không phụ thuộc vào khả năng tính nhẩm của LLM.

2. **Phần nào do model diễn giải?**
   - Hiểu yêu cầu tự nhiên của người dùng để trích xuất đường dẫn file và ngưỡng giờ.
   - Nhận diện khi nào yêu cầu bị thiếu ngưỡng để chủ động hỏi lại người dùng.
   - Diễn giải ý nghĩa nghiệp vụ từ JSON kết quả của script: đưa ra nhận xét, đánh giá tình trạng quá tải và đề xuất phương án xử lý (ví dụ: điều chuyển công việc, kiểm tra lại quy trình nhập liệu).
   - Định dạng và tổng hợp dữ liệu thành báo cáo Markdown chuyên nghiệp theo mẫu template.

3. **Nếu sửa script nhưng không cập nhật skill và reference, báo cáo có thể sai hoặc thiếu thông tin gì?**
   - **Lỗi thực thi dòng lệnh:** Agent không biết tham số mới `--max-hours` là bắt buộc, sẽ tiếp tục gọi lệnh cũ thiếu `--max-hours` $\rightarrow$ Script bị lỗi exit code 2 (do argparse chặn) và agent không hoàn thành nhiệm vụ.
   - **Bỏ sót thông tin quan trọng trong báo cáo:** Script đã tính được `hours_by_owner`, `overloaded_owners` và `excluded_rows`, nhưng nếu `report-template.md` không được cập nhật các mục này, Model sẽ không biết đưa các bảng này vào báo cáo, khiến báo cáo thiếu hoàn toàn thông tin tổng giờ và danh sách quá tải.
   - **Ảo giác hoặc hành vi sai:** Agent không biết nguyên tắc phải hỏi lại khi thiếu ngưỡng, có thể tự tiện bịa ra một ngưỡng ngẫu nhiên (ví dụ tự đoán là 8 hoặc 40) hoặc cố gắng tự tính bằng mắt dẫn đến lỗi cộng trùng giờ (như lỗi Lan = 14 giờ).
