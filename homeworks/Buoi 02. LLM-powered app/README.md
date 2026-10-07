# BTVN Buổi 02: Xây Dựng Ứng Dụng Issue Triage Mini-App

Dự án nhỏ minh họa toàn bộ các nguyên lý cốt lõi của một **LLM-Powered App** được học trong Buổi 02:
- **Prompt Template:** Tách biệt chỉ thị và dữ liệu bằng cấu trúc thẻ XML.
- **Function Calling / Tool Use:** Mô hình phát hiện sự cố cần kiểm tra team sở hữu và đề xuất gọi hàm `get_component_owner`.
- **Structured Output:** Ép buộc mô hình trả về dữ liệu đúng định dạng qua `Pydantic` Model (`IssueTriage`).
- **Application Validation:** Kiểm tra kiểu dữ liệu và ràng buộc logic ngay tại mã nguồn Python.
- **In vết thực thi (Execution Trace):** Hiển thị rõ ràng chu trình từ khi nhận issue, gọi tool, nhận kết quả và chốt phân loại.

---

## 📁 Cấu Trúc Thư Mục

```text
Buoi 02. LLM-powered app/
├── .env                  # Chứa GEMINI_API_KEY (không commit lên Git)
├── .env.example          # Mẫu biến môi trường
├── requirements.txt      # Danh sách thư viện: google-genai, pydantic, python-dotenv
├── main.py               # Mã nguồn chính của ứng dụng
├── README.md             # Hướng dẫn sử dụng & giải thích
└── docs/
    └── uoc_tinh_chi_phi.html  # Báo cáo ước tính chi phí cho 10.000 issue/tháng
```

---

## 🚀 Hướng Dẫn Cài Đặt & Chạy

### 1. Cài đặt các thư viện phụ thuộc:
```bash
pip install -r requirements.txt
```

### 2. Cấu hình API Key:
Mở file `.env` và điền API key của Gemini:
```env
GEMINI_API_KEY=your_gemini_api_key_here
```

### 3. Chạy ứng dụng:
```bash
python main.py
```

---

## 🖥️ Vết Thực Thi Mẫu (Execution Trace)

Khi chạy `python main.py` với kịch bản sự cố thanh toán:

```text
================================================================================
📥 [INPUT ISSUE]
Từ lúc 14:30 hôm nay, nút thanh toán thẻ Visa/Mastercard bị trả mã lỗi HTTP 500 với mọi giao dịch. Tỉ lệ thất bại 100%, khách hàng không mua được hàng.
================================================================================

[TRACE 1] 🚀 Gửi Prompt Template tới Gemini (Model: gemini-3.6-flash)...
[TRACE 2] 🤖 LLM phát tín hiệu Tool Call: 'get_component_owner'
          - Tham số: {'component': 'payment'}
[TRACE 3] ⚙️ Application đang thực thi hàm: get_component_owner('payment')...
          -> Kết quả thực thi (tool_result): 'checkout-platform'
[TRACE 4] 🔄 Gửi yêu cầu sinh Structured Output (Pydantic IssueTriage)...
[TRACE 5] 📄 Nhận JSON thô từ Model:
{"status":"classified","severity":"P0","component":"payment","needs_urgent_response":true,"reason":"Tính năng thanh toán thẻ Visa/Mastercard bị tê liệt hoàn toàn với lỗi HTTP 500 và tỉ lệ thất bại 100%, khách hàng không thể thực hiện giao dịch."}
[TRACE 6] ✅ Application Validate thành công qua Pydantic!

================================================================================
📊 [KẾT QUẢ ĐÃ CHUẨN HÓA VÀ XÁC THỰC]
{
  "status": "classified",
  "severity": "P0",
  "component": "payment",
  "needs_urgent_response": true,
  "reason": "Tính năng thanh toán thẻ Visa/Mastercard bị tê liệt hoàn toàn với lỗi HTTP 500 và tỉ lệ thất bại 100%, khách hàng không thể thực hiện giao dịch."
}
📢 [ĐIỀU PHỐI TICKET] -> Chuyển ngay tới đội ngũ: [CHECKOUT-PLATFORM]
================================================================================
```

---

## 📊 Báo Cáo Chi Phí (Slide 69)
Xem chi tiết file phân tích và bảng tính chi phí tại:  
👉 [`docs/uoc_tinh_chi_phi.html`](docs/uoc_tinh_chi_phi.html)
- Tổng token trung bình mỗi issue: **~655 tokens** (550 input, 105 output).
- Chi phí ước tính cho **10.000 issues/tháng**: **~$0.73 USD** (~18.250 VNĐ) với Gemini Flash hoặc **~$1.18 USD** với GPT Luna.
