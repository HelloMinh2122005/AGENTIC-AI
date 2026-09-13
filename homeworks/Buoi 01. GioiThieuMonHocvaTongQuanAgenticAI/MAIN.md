# BTVN-01: Hãy phân tích 1 hệ thống AI bạn đang dùng

## 1. Phân loại hệ thống và lập luận đủ 3 tiêu chí (4 điểm)

- **Tên hệ thống AI lựa chọn:** **Antigravity** (AI Coding Agent & IDE Pair Programmer) của Google.

- **Phân loại:** **Agentic System** (Hệ thống Agent).

### Lập luận qua 3 tiêu chí:
1. **Ai quyết định bước tiếp theo?**: **Model** — vì không có luồng code cố định từ trước, model tự phân tích ngữ cảnh và quyết định gọi tool nào tiếp theo tại thời điểm chạy (runtime). *Ví dụ:* Khi người dùng yêu cầu *"tìm đoạn code xử lý JWT"*, model sẽ chọn gọi tool `grep_search`; hoặc khi người dùng yêu cầu *"chạy thử test case và báo kết quả"*, model sẽ tự quyết định gọi tool `run_command` rồi đọc kết quả trả về để phán đoán bước kế tiếp.
2. **Ai giữ trạng thái (state)?**: **Hệ thống** — vì hệ thống (Harness) trực tiếp quản lý state qua task list, artifacts (`implementation_plan.md`, logs) và phiên làm việc bền vững (persistent terminal session), không phó mặc hoàn toàn cho context window hữu hạn của model.
3. **Ai dừng vòng lặp?**: **Model + Trần cứng từ hệ thống** — vì model tự đánh giá hoàn thành nhiệm vụ để dừng gọi tool (xuất câu trả lời kết luận), đồng thời hệ thống có trần cứng (timeout lệnh, giới hạn token, human approval / kill task) để chặn nguy cơ lặp vô tận.

---

## 2. Phân tích chi tiết một failure mode cụ thể kèm tình huống (3 điểm)

- **Tên Failure Mode:** **Context Saturation & State Drift** *(Ảo giác và trôi dạt trạng thái trong tác vụ nghiên cứu dài hạn / codebase lớn)*.
- **Repository thực tế:** [HelloMinh2122005/NCKH-CT-Reconstruction](https://github.com/HelloMinh2122005/NCKH-CT-Reconstruction.git) (Dự án NCKH: Tái tạo ảnh cắt lớp CT góc giới hạn - Limited-Angle CT Reconstruction).
- **Tình huống thực tế:**
  - *Bối cảnh:* Codebase nghiên cứu có cấu trúc nhiều tầng gồm nhiều mô hình Deep Learning phức tạp (`LEARN_Mamba`, `LEARN_LongNet`, `DuDoTrans`), điều phối hàng chục job huấn luyện trên cụm máy chủ GPU Slurm và đòi hỏi bảo toàn nghiêm ngặt các docstring/comment giải thích công thức toán, kích thước tensor.
  - *Diễn biến lỗi:* Khi phiên làm việc kéo dài qua nhiều lượt trao đổi, cửa sổ ngữ cảnh (context window) bị bão hòa, mô hình bắt đầu bị trôi dạt trạng thái ("State Drift") — quên mất tiến trình hiện tại, không nhớ vị trí file/hàm, tự bịa ra đường dẫn script không tồn tại và tự ý xóa/sửa các comment tiếng Việt giải thích kích thước tensor.
  - *Hậu quả:* Gây gián đoạn nghiên cứu, chạy sai job trên cụm cluster và làm sai lệch tính toàn vẹn của mã nguồn nghiên cứu.

---

## 3. Trình bày 2 lớp harness và cơ chế cụ thể (3 điểm)

Để khắc phục triệt để failure mode trên (thay vì cố gắng đổi model), hệ thống cần áp dụng 2 lớp Harness bao bọc:

1. **Lớp 6: State Harness (với cơ chế *Persistent Task Checkpointing* — minh chứng qua `CHECKPOINT.md`):**
   - **Cơ chế:** Lưu trữ trạng thái tác vụ, tiến độ các job Slurm (`COMPLETED`, `FAILED`), checklist công việc và các tham số hình học CT đã chốt xuống tệp lưu trữ trên hệ thống (Disk/System State) thay vì phó mặc cho context chat. Đầu mỗi phiên làm việc, Agent bắt buộc phải đọc file checkpoint này để khôi phục chính xác 100% tiến trình trước khi thực thi tiếp.
2. **Lớp 3: Skills / Lớp 1: Context Harness (với cơ chế *Ground Rules Ingestion* — minh chứng qua `AGENTS.md`):**
   - **Cơ chế:** Đóng gói toàn bộ quy tắc nghiệp vụ bất biến vào tệp chỉ dẫn chuẩn hóa (bảo tồn nguyên vẹn chú thích tiếng Việt, bắt buộc kiểm tra VRAM qua script `gpu_check.sh`, chuẩn hóa thư mục lưu log `%j.out`). Tầng Harness tự động chắt lọc và nạp bộ quy tắc này vào đầu context ở mỗi session, ngăn chặn model tự suy diễn hay vi phạm quy định khi ngữ cảnh phình to.