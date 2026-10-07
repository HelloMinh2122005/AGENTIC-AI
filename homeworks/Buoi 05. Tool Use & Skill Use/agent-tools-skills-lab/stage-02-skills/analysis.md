# Báo cáo phân tích Block 1: Tra cứu chính sách đúng phiên bản

**Học phần:** Agentic AI Engineering (D05 - Tool Use & Skill Use)  
**Nhóm sinh viên:** Phan Đình Minh (MSSV: 23520949)  
**Project:** `stage-02-skills` (kế thừa từ `stage-01-files`)

---

## 1. Kết quả kiểm tra Tool `list_files` trực tiếp

Tool `list_files(path: str)` được cài đặt tại `tools/files.py`, export qua `tools/__init__.py` và đăng ký trong `agent.py`:
- Liệt kê trực tiếp không đệ quy.
- Định dạng trả về: `{"ok": true, "path": ..., "entries": [{"name": ..., "path": ..., "type": ...}]}` sắp xếp theo tên.
- Bảo vệ an toàn: chặn path traversal `..`, absolute path, symlink escape ra ngoài workspace.

### Bảng kết quả kiểm thử trực tiếp:
| Trường hợp gọi tool | Tham số `path` | Kết quả thực tế | Trạng thái |
|---|---|---|---|
| **Thư mục hợp lệ** | `data/policies` | `{"ok": true, "path": "data/policies", "entries": [...]}` | Thành công |
| **Thư mục gốc workspace** | `.` hoặc `""` | `{"ok": true, "path": ".", "entries": [...]}` | Thành công |
| **Đường dẫn là file** | `data/policies/policy-before-oct.md` | `{"ok": false, "error": {"code": "NOT_A_DIRECTORY", ...}}` | Báo lỗi đúng yêu cầu |
| **Đường dẫn không tồn tại** | `data/khong-co-thu-muc` | `{"ok": false, "error": {"code": "DIR_NOT_FOUND", ...}}` | Báo lỗi đúng yêu cầu |
| **Thoát workspace (traversal)** | `../outside` | `{"ok": false, "error": {"code": "PATH_OUTSIDE_WORKSPACE", ...}}` | Chặn và báo lỗi đúng |

Unit tests kiểm thử tự động đạt: **21/21 passed** trong `tests/test_files.py`.

---

## 2. Kết quả từng trường hợp kiểm thử Agent & Vị trí bằng chứng trong Trace

Các trace được lưu tại thư mục `traces/` theo chuẩn Observer & TraceWriter:

### Trường hợp A: Mua trước ngày đổi chính sách (28/09/2026, hoàn 06/10/2026, chưa kích hoạt)
- **Câu hỏi:** *"Tôi mua ngày 28/09/2026, yêu cầu hoàn ngày 06/10/2026, chưa kích hoạt. Tôi có được hoàn không?"*
- **Kết quả:** Không đủ điều kiện hoàn tiền (8 ngày vượt quá thời hạn 7 ngày quy định).
- **File trace:** `traces/20261007-222203_d01f1bc7_turn01_62d6a13d.jsonl`
- **Vị trí bằng chứng trong trace:**
  - Dòng 1 (`sequence 1`): `user_submitted` nhận câu hỏi của người dùng.
  - Dòng 3-5 (`sequence 3-5`): Model nhận diện tác vụ, gọi `read_file` đọc `skills/refund-policy/SKILL.md`.
  - Dòng 7-10 (`sequence 7-10`): Model gọi song song `list_files` tại `data/policies` và `read_file` đọc `skills/refund-policy/references/answer-template.md`.
  - Dòng 12-14 (`sequence 12-14`): Model đọc nội dung `data/policies/policy-before-oct.md`.
  - Dòng 15 (`sequence 15`): Model xuất câu trả lời theo đúng template, dẫn chứng thời gian 8 ngày và trích dẫn file `data/policies/policy-before-oct.md`.

### Trường hợp B (Sau khi đổi tên file chính sách): Mua từ ngày đổi chính sách (02/10/2026, hoàn 12/10/2026, chưa kích hoạt)
- **Đổi tên:** `policy-before-oct.md` → `chinh-sach-cu.md`, `policy-from-oct.md` → `chinh-sach-moi.md`.
- **Câu hỏi:** *"Tôi mua ngày 02/10/2026, yêu cầu hoàn ngày 12/10/2026, chưa kích hoạt. Tôi có được hoàn không?"*
- **Kết quả:** Đủ điều kiện hoàn tiền, không mất phí (10 ngày $\le$ 14 ngày, sản phẩm chưa kích hoạt).
- **File trace:** `traces/20261007-222203_7d47fa6b_turn01_917e603f.jsonl`
- **Vị trí bằng chứng trong trace:**
  - Dòng 3-5: Gọi `read_file("skills/refund-policy/SKILL.md")`.
  - Dòng 7-10: Gọi `list_files("data/policies")` → Trả về danh sách gồm `chinh-sach-cu.md` và `chinh-sach-moi.md`.
  - Dòng 12-14: Model đọc `data/policies/chinh-sach-moi.md` (chọn file mới phát hiện động qua `list_files`).
  - Dòng 15: Xuất kết quả đúng điều kiện, không phí, trích dẫn đúng căn cứ `data/policies/chinh-sach-moi.md`.

### Trường hợp C: Thiếu thông tin đầu vào
- **Câu hỏi:** *"Tôi mua ngày 02/10/2026, muốn hoàn ngày 12/10/2026."*
- **Kết quả:** Agent hỏi lại người dùng về trạng thái kích hoạt, không tự giả định "chưa kích hoạt".
- **File trace:** `traces/20261007-222203_18eba233_turn01_75fa89c1.jsonl`
- **Vị trí bằng chứng trong trace:**
  - Dòng 3-5: Gọi `read_file("skills/refund-policy/SKILL.md")`.
  - Dòng 7: Model phản hồi yêu cầu người dùng làm rõ trạng thái kích hoạt của sản phẩm trước khi đưa ra kết luận.

---

## 3. Trả lời câu hỏi cuối bài (Block 1)

### Câu hỏi:
> *Vì sao cần tool để tìm file và skill để hướng dẫn chọn chính sách? Nếu agent chưa có tool tìm file, việc sửa prompt có giải quyết được yêu cầu đổi tên file không? Giải thích.*

### Trả lời:
1. **Vì sao cần tool để tìm file (`list_files`)?**
   - Không gian file trong thực tế là động (dynamic): tên file, cấu trúc thư mục hoặc phiên bản tài liệu có thể thay đổi bất kỳ lúc nào mà prompt không thể lường trước.
   - Tool `list_files` cung cấp khả năng **nhận thức môi trường (environmental sensing)**: Agent có thể truy vấn cấu trúc thư mục tại thời điểm thực thi (runtime) để biết chính xác những file nào đang tồn tại, thay vì giả định mù quáng (blind assumption).

2. **Vì sao cần skill để hướng dẫn chọn chính sách?**
   - Skill chứa đựng **quy trình nghiệp vụ chuyên biệt (domain knowledge / business workflow)** mà không làm phình to system prompt ban đầu (progressive context loading).
   - Skill hướng dẫn Agent các nguyên tắc logic quan trọng:
     - Phải hỏi lại nếu thiếu thông tin (tránh tự suy đoán).
     - Quy tắc đối chiếu mốc ngày mua để chọn chính sách.
     - Cách tính số ngày lịch và format câu trả lời theo chuẩn template.

3. **Nếu agent chưa có tool tìm file, việc sửa prompt có giải quyết được yêu cầu đổi tên file không?**
   - **Không thể giải quyết triệt để.**
   - *Giải thích:* Nếu không có tool `list_files`, Agent chỉ có `read_file` (vốn đòi hỏi phải biết trước đường dẫn chính xác). Nếu người dùng hoặc hệ thống đổi tên file (ví dụ từ `policy-from-oct.md` thành `chinh-sach-moi.md` hay `refund_v2.md`), việc sửa system prompt chỉ là "hard-code" tên mới vào prompt. Mỗi lần đổi tên lại phải sửa prompt thủ công, vi phạm nguyên tắc tự trị (autonomy) của Agent. Khi gặp một tên file bất kỳ không có trong prompt, Agent sẽ hoàn toàn mất khả năng truy cập tài liệu (`FILE_NOT_FOUND`) và rơi vào failure mode ảo giác (hallucination). Tool `list_files` là điều kiện tiên quyết để giải quyết bài toán thích ứng động này.
