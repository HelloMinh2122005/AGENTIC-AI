"""
HỆ THỐNG PHÂN LOẠI SỰ CỐ TỰ ĐỘNG (ISSUE TRIAGE MINI-APP)
BTVN Buổi 02: Các nguyên lý cơ bản của LLM-powered app

Quy trình thực thi:
1. Nhận mô tả sự cố (Issue Description).
2. Định hình Prompt Template sử dụng cấu trúc thẻ XML.
3. Gửi request tới Gemini API kèm theo định nghĩa Tool (get_component_owner).
4. Model đề xuất Tool Call -> Application thực thi hàm nội bộ -> Gửi Tool Result ngược lại.
5. Model trả về dữ liệu có cấu trúc (Structured Output) theo Schema Pydantic.
6. Application Validate và in toàn bộ vết thực thi (Execution Trace).
"""

import os
import json
import logging
from typing import Literal
from dotenv import load_dotenv
from pydantic import BaseModel, Field, ValidationError
from google import genai
from google.genai import types
from google.genai import models

# Vô hiệu hóa cảnh báo AFC mặc định vì hệ thống tự quản lý application-controlled tool execution
models.Models._logged_afc_warning = True
logging.getLogger("google_genai.models").setLevel(logging.ERROR)

# Tải biến môi trường từ file .env
load_dotenv()


# ==============================================================================
# 1. ĐỊNH NGHĨA SCHEMA DỮ LIỆU ĐẦU RA (PYDANTIC MODEL)
# ==============================================================================
class IssueTriage(BaseModel):
    status: Literal["classified", "insufficient_data", "out_of_scope"] = Field(
        description="Trạng thái phân loại: classified (đủ dữ liệu), insufficient_data (thiếu thông tin), out_of_scope (ngoài phạm vi)"
    )
    severity: Literal["P0", "P1", "P2", "P3"] | None = Field(
        default=None,
        description="Mức độ nghiêm trọng từ P0 (cao nhất) đến P3 (thấp nhất), null nếu không phân loại được"
    )
    component: str | None = Field(
        default=None,
        description="Tên thành phần bị lỗi (ví dụ: payment, auth, database, frontend)"
    )
    needs_urgent_response: bool = Field(
        default=False,
        description="True nếu sự cố nghiêm trọng cần đội ngũ kỹ thuật xử lý ngay lập tức (thường là P0/P1)"
    )
    reason: str = Field(
        description="Lý do ngắn gọn giải thích phân loại dựa trên dữ liệu sự cố"
    )


# ==============================================================================
# 2. KHAI BÁO CÔNG CỤ (TOOL USE / FUNCTION CALLING)
# ==============================================================================
def get_component_owner(component: str) -> str:
    """Trả về team chịu trách nhiệm cho component."""
    mapping = {
        "payment": "checkout-platform",
        "auth": "identity-team",
        "database": "data-infra",
        "frontend": "ui-team",
        "api": "backend-core"
    }
    return mapping.get(component.lower().strip(), "general-support")


# Tool Declaration gửi lên Gemini API
COMPONENT_TOOL = types.Tool(
    function_declarations=[
        types.FunctionDeclaration(
            name="get_component_owner",
            description="Tìm kiếm đội ngũ kỹ thuật chịu trách nhiệm cho một component cụ thể.",
            parameters=types.Schema(
                type="OBJECT",
                properties={
                    "component": types.Schema(
                        type="STRING",
                        description="Tên component hệ thống bị ảnh hưởng (ví dụ: payment, auth, database)"
                    )
                },
                required=["component"]
            )
        )
    ]
)


# ==============================================================================
# 3. PROMPT TEMPLATE (CHUẨN HÓA VỚI THẺ XML)
# ==============================================================================
def build_prompt(issue_description: str) -> str:
    return f"""<role>
Bạn là chuyên gia kỹ thuật phụ trách phân loại sự cố hệ thống (Issue Triage Engineer).
</role>

<context>
Hệ thống phần mềm thương mại điện tử trực tuyến đang vận hành trên Production.
Các mức độ nghiêm trọng:
- P0: Toàn bộ hệ thống hoặc tính năng thanh toán tê liệt, tỉ lệ thất bại 100%, mất tiền người dùng.
- P1: Tính năng cốt lõi bị lỗi nghiêm trọng, ảnh hưởng diện rộng nhưng có thể vẫn còn một phần luồng chạy.
- P2: Lỗi chức năng phụ, có workaround (cách khắc phục tạm thời).
- P3: Lỗi giao diện nhỏ, sai màu sắc icon, lỗi hiển thị font.
</context>

<task>
1. Phân tích mô tả sự cố trong thẻ <input>.
2. Nếu xác định được component bị lỗi, HÃY GỌI HÀM get_component_owner để tìm team phụ trách.
3. Sau khi có thông tin, hãy phân loại sự cố theo đúng các tiêu chí.
</task>

<constraints>
- Nếu mô tả quá ngắn, mơ hồ hoặc thiếu mã lỗi/ngữ cảnh, đặt status = "insufficient_data" và severity = null.
- Nếu nội dung không liên quan đến phần mềm, đặt status = "out_of_scope" và severity = null.
- Tuyệt đối không tự suy đoán nếu không có cơ sở dữ liệu.
</constraints>

<input>
{issue_description}
</input>
"""


# ==============================================================================
# 4. HÀM ĐIỀU PHỐI TRIAGE CHÍNH (APPLICATION LOGIC & TRACE)
# ==============================================================================
def triage_issue(issue_description: str) -> tuple[IssueTriage, str | None]:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("Không tìm thấy GEMINI_API_KEY trong file .env hoặc biến môi trường!")

    client = genai.Client(api_key=api_key)
    prompt = build_prompt(issue_description)

    print("\n" + "=" * 80)
    print("📥 [INPUT ISSUE]")
    print(issue_description.strip())
    print("=" * 80)

    print("\n[TRACE 1] 🚀 Gửi Prompt Template tới Gemini (Model: gemini-3.6-flash)...")

    # BƯỚC 1: Gọi model lần đầu với danh sách Tools
    resp1 = client.models.generate_content(
        model=os.getenv("GEMINI_MODEL") or "gemini-3.5-flash-lite",
        contents=prompt,
        config=types.GenerateContentConfig(
            tools=[COMPONENT_TOOL],
            temperature=0.0,  # Đảm bảo tính ổn định cao nhất
            automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
        )
    )

    team_owner = None
    contents_for_step2 = [
        types.Content(role="user", parts=[types.Part.from_text(text=prompt)]),
        resp1.candidates[0].content
    ]

    # BƯỚC 2: Kiểm tra xem Model có yêu cầu Tool Call hay không
    if resp1.function_calls:
        for call in resp1.function_calls:
            print(f"[TRACE 2] 🤖 LLM phát tín hiệu Tool Call: '{call.name}'")
            print(f"          - Tham số: {call.args}")

            if call.name == "get_component_owner":
                comp = call.args.get("component", "unknown")
                
                # Application trực tiếp thực thi hàm nội bộ
                print(f"[TRACE 3] ⚙️ Application đang thực thi hàm: get_component_owner('{comp}')...")
                team_owner = get_component_owner(comp)
                print(f"          -> Kết quả thực thi (tool_result): '{team_owner}'")

                # Đưa kết quả tool vào ngữ cảnh gửi ngược lại cho LLM
                contents_for_step2.append(
                    types.Content(
                        role="user",
                        parts=[
                            types.Part.from_function_response(
                                name=call.name,
                                response={"owner": team_owner}
                            )
                        ]
                    )
                )
    else:
        print("[TRACE 2] ℹ️ Model không yêu cầu gọi Tool (Không tìm thấy component hoặc issue ngoài phạm vi).")

    # BƯỚC 3: Yêu cầu kết quả cuối cùng theo đúng JSON Schema Pydantic
    print("[TRACE 4] 🔄 Gửi yêu cầu sinh Structured Output (Pydantic IssueTriage)...")
    contents_for_step2.append(
        types.Content(
            role="user",
            parts=[types.Part.from_text(text="Dựa vào toàn bộ thông tin trên, hãy trả về kết quả phân loại sự cố cuối cùng.")]
        )
    )

    resp2 = client.models.generate_content(
        model=os.getenv("GEMINI_MODEL") or "gemini-3.5-flash-lite",
        contents=contents_for_step2,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=IssueTriage,
            temperature=0.0,
            automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
        )
    )

    raw_json = resp2.text
    print(f"[TRACE 5] 📄 Nhận JSON thô từ Model:\n{raw_json}")

    # BƯỚC 4: Application Validation qua Pydantic
    try:
        validated_triage = IssueTriage.model_validate_json(raw_json)
        print("[TRACE 6] ✅ Application Validate thành công qua Pydantic!")
    except ValidationError as e:
        print(f"[TRACE 6] ❌ Lỗi Validation: {e}")
        raise e

    return validated_triage, team_owner


# ==============================================================================
# 5. CHẠY THỬ NGHIỆM VỚI CÁC TRƯỜNG HỢP MẪU (TEST CASES)
# ==============================================================================
if __name__ == "__main__":
    # Danh sách các kịch bản kiểm thử mẫu
    sample_issues = [
        # Case 1: Lỗi thanh toán khẩn cấp (P0)
        "Từ lúc 14:30 hôm nay, nút thanh toán thẻ Visa/Mastercard bị trả mã lỗi HTTP 500 với mọi giao dịch. Tỉ lệ thất bại 100%, khách hàng không mua được hàng.",
        
        # Case 2: Lỗi giao diện nhỏ (P3)
        "Nút đăng xuất trên trang profile bị lệch font chữ và sai màu icon trên trình duyệt Safari phiên bản cũ.",
        
        # Case 3: Thiếu dữ liệu (insufficient_data)
        "App bị lỗi rồi admin ơi, vào xem hộ tôi với!",
        
        # Case 4: Ngoài phạm vi (out_of_scope)
        "Chỉ giúp tôi cách nấu phở bò Hà Nội chuẩn vị tại nhà với."
    ]

    print("================================================================================")
    print("🚀 BẮT ĐẦU CHẠY THỰC NGHIỆM ISSUE TRIAGE MINI-APP VỚI GEMINI API")
    print("================================================================================")

    # Chạy thử kịch bản chính (Case 1)
    result, owner = triage_issue(sample_issues[0])

    print("\n" + "=" * 80)
    print("📊 [KẾT QUẢ ĐÃ CHUẨN HÓA VÀ XÁC THỰC]")
    print(json.dumps(result.model_dump(), indent=2, ensure_ascii=False))
    if owner:
        print(f"📢 [ĐIỀU PHỐI TICKET] -> Chuyển ngay tới đội ngũ: [{owner.upper()}]")
    print("=" * 80)
