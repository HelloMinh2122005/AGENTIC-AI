---
name: refund-policy
description: Tra cứu và áp dụng chính sách hoàn tiền theo ngày mua của khách hàng. Dùng khi người dùng hỏi về điều kiện, thời hạn hoàn tiền, mức phí hoàn tiền hoặc quyền lợi trả hàng hoàn tiền của đơn hàng.
---

# Refund Policy

Tra cứu và áp dụng chính sách hoàn tiền chính xác cho đơn hàng theo ngày mua.

## Quy trình thực hiện

1. **Kiểm tra thông tin đầu vào:**
   Cần có đủ 3 thông tin từ người dùng:
   - Ngày mua hàng (purchase date).
   - Ngày yêu cầu hoàn tiền (refund request date).
   - Trạng thái kích hoạt của sản phẩm (activated status).
   
   > **Quan trọng:** Nếu người dùng chưa cung cấp đủ một trong 3 thông tin trên (ví dụ không rõ ngày mua, ngày yêu cầu hoặc chưa nêu sản phẩm đã kích hoạt hay chưa), **phải hỏi lại người dùng để làm rõ trước khi đưa ra kết luận**. Tuyệt đối không tự suy đoán (ví dụ không tự giả định "chưa kích hoạt").

2. **Tìm tài liệu chính sách:**
   - Dùng tool `list_files` với đường dẫn `data/policies` để liệt kê danh sách tài liệu chính sách hiện có.
   - Không được viết cố định tên file vì tên file có thể bị thay đổi.
   - Dùng tool `read_file` để đọc nội dung các file chính sách tìm được nhằm xác định phạm vi hiệu lực của từng chính sách.

3. **Chọn chính sách và đánh giá điều kiện:**
   - Căn cứ vào **ngày mua** của khách hàng để chọn chính sách áp dụng:
     - Mua trước ngày `2026-10-01`: áp dụng chính sách trước tháng 10.
     - Mua từ ngày `2026-10-01` trở đi (bao gồm cả ngày này): áp dụng chính sách từ tháng 10.
   - Tính số ngày chênh lệch lịch giữa ngày yêu cầu hoàn tiền và ngày mua (Số ngày = Ngày yêu cầu - Ngày mua).
   - Điều kiện hoàn tiền:
     - Nếu sản phẩm đã kích hoạt: **Không được hoàn tiền**.
     - Nếu số ngày $\le$ thời hạn quy định trong chính sách áp dụng: **Đủ điều kiện hoàn tiền**.
     - Nếu số ngày > thời hạn quy định: **Không đủ điều kiện hoàn tiền** (do quá hạn).
   - Phí hoàn tiền: Áp dụng đúng quy định trong chính sách đã chọn (10% hoặc không thu phí).

4. **Định dạng câu trả lời:**
   - Đọc mẫu trình bày tại `references/answer-template.md` trong thư mục skill này (`skills/refund-policy/references/answer-template.md`).
   - Phản hồi cho người dùng phải có: chính sách áp dụng, số ngày đã qua, kết luận đủ/không đủ điều kiện, phí hoàn tiền (nếu đủ), và đường dẫn file tài liệu làm căn cứ.
