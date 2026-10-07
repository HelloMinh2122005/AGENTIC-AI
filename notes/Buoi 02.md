# Buổi 02: Các nguyên lý cơ bản của LLM-Powered App

Tài liệu ghi chép và diễn giải chi tiết toàn bộ phần lý thuyết bài giảng Buổi 02. Tài liệu này giúp định hình tư duy lập trình khi chuyển từ việc "chat với LLM" sang việc "xây dựng hệ sinh thái phần mềm tích hợp LLM".

---

## 🗺️ Bản đồ tổng quan bài giảng (Mindmap)

```mermaid
mindmap
  root("LLM-Powered App")
    ("1. LLM API & Cơ chế")
      ["Messages: system, user, assistant, tool"]
      ["Token & Tokenizer (Lưu ý tiếng Việt)"]
      ["Context Window: Lost-in-the-middle & Context rot"]
      ["Generation Params: temperature, top_p"]
      ["Chi phí Multi-step & Prompt Caching"]
    ("2. Prompt & Context Engineering")
      ["Prompt Engineering: Cách hỏi & mô tả task"]
      ["Context Engineering: Chọn lọc dữ liệu nạp"]
      ["Cấu trúc Prompt chuẩn: Thẻ XML"]
      ["In-context Learning: Zero, Few-shot, CoT"]
    ("3. Structured Output")
      ["Giải quyết bế tắc của Prose output"]
      ["JSON Schema & Pydantic BaseModel"]
      ["Prompt-only vs Constrained Output"]
      ["Kiểm tra cấu trúc != Kiểm tra ngữ nghĩa"]
    ("4. Function Calling & Tool Use")
      ["Structured Output (dữ liệu) vs Tool Call (hành động)"]
      ["Quy trình: Model đề xuất, App thực thi"]
      ["Tool Schema & Tool Validation"]
    ("5. Bước đệm sang AI Agent")
      ["LLM-powered app: Luồng cố định (Hard-coded)"]
      ["AI Agent: Vòng lặp tự trị (Agent Loop)"]
```

---

## PHẦN 1: LLM-POWERED APP & CƠ CHẾ TƯƠNG TÁC API

### 1. Bản chất của một LLM-Powered App
Một **LLM-powered app** là phần mềm trong đó mã nguồn ứng dụng (Application code) đóng vai trò điều phối:
1. Gửi dữ liệu đầu vào tới LLM API dưới dạng request có cấu trúc.
2. Nhận kết quả phản hồi từ LLM và đưa kết quả này vào luồng logic (`if-else`, truy vấn DB, gọi service tiếp theo) của phần mềm.

#### Bế tắc của văn bản tự nhiên (Prose Output):
* **Con người:** Đọc hiểu tốt các câu chữ tự nhiên như: *"Lỗi này có vẻ nghiêm trọng, có thể là P0 hoặc P1 tùy mức độ..."*.
* **Phần mềm:** Không thể điều kiện hóa (`if/else`) bằng câu chữ mơ hồ. Nếu dùng Regex hay tìm chuỗi con `if "P0" in response:` thì hệ thống sẽ rất mong manh, dễ vỡ khi văn phong model thay đổi. Phần mềm bắt buộc phải nhận được dữ liệu có cấu trúc ổn định.

---

### 2. Chu trình tương tác với LLM API

```mermaid
sequenceDiagram
    autonumber
    participant App as "Application (Mã nguồn của bạn)"
    participant API as "LLM API (OpenAI / Gemini / v.v.)"

    Note over App: Chuẩn bị Request:<br/>- model<br/>- messages [system, user]<br/>- parameters (temperature, top_p)<br/>- tools / schemas (nếu có)
    App->>API: Gửi API Request (JSON)
    Note over API: Tokenization & Giải mã (Decoding)
    API-->>App: Trả về Response:<br/>- Content text / Structured Data<br/>- Tool Calls (nếu có)<br/>- Usage info (tokens)<br/>- Finish reason
    Note over App: Phân tích response để chạy tiếp logic nghiệp vụ
```

---

### 3. Phân định vai trò trong `messages`

Cấu trúc hội thoại chuẩn mực gửi lên model gồm danh sách các đối tượng message với vai trò rõ ràng:

| Role (Vai trò) | Mục đích & Trách nhiệm |
| :--- | :--- |
| **`system` / `developer`** | Thiết lập chỉ thị nền tảng: quy định vai trò, nguyên tắc làm việc, giọng điệu, các ràng buộc cấm vi phạm. Model sẽ bám theo chỉ thị này suốt phiên làm việc. |
| **`user`** | Đầu vào hoặc yêu cầu cụ thể từ người dùng hoặc do ứng dụng nạp vào ở lượt gọi hiện tại. |
| **`assistant`** | Phản hồi trước đó của chính LLM trong cùng phiên (được ứng dụng lưu lại và gửi kèm để duy trì ngữ cảnh nhiều lượt - multi-turn). |
| **`tool`** | Kết quả thực thi thực tế của công cụ được gửi ngược lại cho model sau khi ứng dụng chạy xong hàm mà model yêu cầu. |

---

### 4. Token, Context Window và Chi phí

#### A. Token & Tokenizer
* LLM xử lý ngôn ngữ dưới dạng các mảnh từ gọi là **Token**, không phải ký tự hay từ nguyên vẹn.
* **Lưu ý đặc biệt về Tiếng Việt:** Do các bộ tokenizer phổ biến (như `cl100k_base`, `o200k_base`) được tối ưu cho tiếng Anh, văn bản tiếng Việt thường bị băm thành nhiều mảnh nhỏ hơn, dẫn tới việc tiêu tốn **1.6× đến 2.4× lượng token** so với nội dung tiếng Anh tương đương.
* *Tuyệt đối không dùng `len(text.split())` để ước lượng chi phí token.*

#### B. Context Window & Các hiện tượng suy giảm hiệu năng
Context Window là tổng lượng token tối đa mà mô hình có thể tiếp nhận và sinh ra trong một lần gọi duy nhất.

```mermaid
graph LR
    A["Đầu Context (Instruction nền)"] -->|Nhớ rất tốt| B["Đoạn giữa (Nhiễu / Lịch sử dài)"]
    B -->|Dễ bị lãng quên: Lost-in-the-middle| C["Cuối Context (User Query mới nhất)"]
    C -->|Nhớ rất tốt| D["Đầu ra sinh tiếp"]
```

* **Lost in the middle:** Thông tin quan trọng nằm ở đoạn giữa của một context dài có xác suất bị mô hình bỏ sót cao hơn thông tin nằm ở ngay đầu hoặc cuối context.
* **Context rot:** Khi context bị nhồi nhét quá dài và chứa nhiều thông tin rác, khả năng suy luận logic của model bị giảm sút rõ rệt dù vẫn chưa chạm trần kỹ thuật của context window.

#### C. Chi phí trong quy trình nhiều bước (Multi-step)
Trong một task chạy qua 10 bước:
* Mỗi bước gửi lại 3.000 token nền + 500 token lịch sử mới.
* **Chi phí tính tiền:** Là tổng lượng token của **cả 10 lần gọi cộng lại**, chứ không phải chỉ là token của bước thứ 10.
* **Prompt Caching:** Kỹ thuật của nhà cung cấp API lưu lại bộ nhớ đệm cho phần prefix giống nhau giữa các lần gọi. Caching giúp **giảm tiền và độ trễ**, nhưng **không làm model thông minh hơn**.

---

### 5. Generation Parameters (Tham số điều khiển quá trình sinh)

#### A. Bản chất toán học: LLM chọn từ như thế nào?
Sau khi tiếp nhận câu prompt, tại mỗi bước sinh từ tiếp theo, LLM **không chọn từ ngay lập tức**. Tầng cuối cùng của mô hình sẽ tính toán một bảng phân phối xác suất cho toàn bộ từ điển (khoảng 100.000 token).
*Ví dụ:* Sau câu *"Hôm nay trời nhiều mây, dự báo chiều nay có thể sẽ..."*, xác suất tính được là:
* `"mưa"`: **65%**
* `"dông"`: **20%**
* `"nắng"`: **10%**
* `"gió nhẹ"`: **4.9%**
* `"ăn kem"`: **0.1%**

👉 **Các tham số sinh (Generation Parameters) chính là các "núm vặn" để thay đổi luật chơi của trò bốc thăm token này.**

```mermaid
flowchart TD
    A["Prompt Input"] --> B["LLM tính toán phân phối xác suất từ điển<br/>('mưa': 65%, 'dông': 20%, 'nắng': 10%, 'ăn kem': 0.1%)"]
    
    B --> C{"BƯỚC 1: top_p (Vòng gửi xe)"}
    C -->|"top_p = 0.85<br/>Chỉ giữ 'mưa' (65%) + 'dông' (20%) = 85%<br/>Loại bỏ hẳn: 'nắng', 'ăn kem'"| D["Tập ứng viên tinh hoa"]
    
    D --> E{"BƯỚC 2: Temperature (Cách bốc thăm)"}
    E -->|"T = 0 (Thấp): Luôn lấy từ cao nhất"| F["Chọn 'mưa' (100% chắc chắn)"]
    E -->|"T = 1.0 (Cao): San phẳng tỉ lệ, liều lĩnh hơn"| G["Có cơ hội bốc trúng 'dông'"]
    
    F --> H["Ghép token vào câu & lặp lại bước tiếp"]
    G --> H
    H --> I{"BƯỚC 3: max_tokens (Lưỡi kéo ngắt)"}
    I -->|"Chưa chạm trần"| B
    I -->|"Đạt max_tokens"| K["Dừng ngay lập tức (finish_reason: length)"]
```

---

#### B. `temperature` (Nhiệt độ) – Độ "phiêu lưu" khi bốc thăm
`temperature` ($T$) can thiệp vào hàm Softmax để **phóng đại** hoặc **san phẳng** sự chênh lệch xác suất giữa các từ:

$$P(\text{token}_i) = \frac{e^{z_i / T}}{\sum_j e^{z_j / T}}$$

*Bảng minh họa sự biến thiên xác suất theo nhiệt độ:*

| Token ứng viên | Xác suất gốc | Khi $T = 0$ (Cực lạnh) | Khi $T = 0.7$ (Cân bằng) | Khi $T = 1.5$ (Cực nóng) |
| :--- | :---: | :---: | :---: | :---: |
| `"mưa"` | 65% | **100%** | 55% | 30% |
| `"dông"` | 20% | 0% | 25% | 25% |
| `"nắng"` | 10% | 0% | 13% | 22% |
| `"gió nhẹ"` | 4.9% | 0% | 6.9% | 18% |
| `"ăn kem"` | 0.1% | 0% | 0.1% | 5% |

* **Khi $T = 0$ (Greedy Decoding / Xác định hoàn toàn):**
  * Không còn bốc thăm ngẫu nhiên. Token có xác suất cao nhất luôn luôn thắng ($100\%$).
  * **Đặc tính:** Chạy 100 lần thì cả 100 lần đều trả về **cùng một kết quả giống hệt nhau từng ký tự**.
  * **Ứng dụng:** Viết mã nguồn (Coding), truy vấn SQL, giải Toán, phân loại sự cố (Issue Triage), sinh JSON theo Schema.
* **Khi $T$ cao ($0.8 - 1.2$):**
  * Nhiệt độ cao làm phẳng đồ thị xác suất, thu hẹp khoảng cách giữa token dẫn đầu và token xếp sau. Mô hình dễ bốc trúng các từ bất ngờ, độc đáo hơn.
  * **Đặc tính:** Câu văn phong phú, sáng tạo, nhưng nếu đặt quá cao ($> 1.5$) thì mô hình sẽ nói lảm nhảm, loạn ngữ hoặc sinh ảo giác (hallucination).
  * **Ứng dụng:** Sáng tác văn học, làm thơ, brainstorm ý tưởng chiến dịch marketing.

---

#### C. `top_p` (Nucleus Sampling) – "Bộ lọc vòng gửi xe"
Nếu `temperature` quyết định *cách thức bốc thăm*, thì `top_p` là *luật loại trừ ứng viên trước khi bốc thăm*.

* **Vấn đề đặt ra:** Trong từ điển có hàng ngàn token vô nghĩa hoặc phản cảm (xác suất chỉ $0.001\%$). Dù $T$ có cao thế nào, ta cũng không muốn model vô tình bốc trúng các từ rác này.
* **Cơ chế:** Sắp xếp các token từ xác suất cao xuống thấp và tính tổng tích lũy. Khi tổng vừa chạm ngưỡng $p$, **loại bỏ hoàn toàn tất cả các token còn lại**.
  * *Ví dụ:* Với `top_p = 0.85`, do `"mưa"` ($65\%$) + `"dông"` ($20\%$) = $85\%$, model sẽ loại bỏ toàn bộ `"nắng"`, `"gió nhẹ"`, `"ăn kem"`. Việc bốc thăm chỉ diễn ra giữa `"mưa"` và `"dông"`.
* **Lời khuyên thực tế:** **Chỉ nên điều chỉnh 1 trong 2** (`temperature` hoặc `top_p`), giữ tham số còn lại ở mặc định để tránh hành vi bất thường.

---

#### D. `max_tokens` – "Lưỡi kéo" giới hạn độ dài
* ❌ **Hiểu lầm phổ biến:** Nghĩ rằng đặt `max_tokens = 50` là mô hình sẽ "tóm tắt ngắn gọn câu trả lời trong phạm vi 50 token".
* ✅ **Bản chất thực tế:** Mô hình **không hề biết trước** nó bị giới hạn 50 token và vẫn sinh câu dài dòng như bình thường. Cứ mỗi token sinh ra, bộ đếm giảm đi 1. Đúng đến token thứ 50, API **cắt ngang lập tức** (dù câu đang dang dở).
* Khi bị ngắt cưỡng bức, API trả về trạng thái: `finish_reason: "length"` (thay vì `finish_reason: "stop"` khi kết thúc tự nhiên).

---

#### E. Bảng tra cứu thiết lập tham số chuẩn cho dự án thực tế

| Nhiệm vụ trong hệ thống phần mềm | `temperature` | `top_p` | Lý do kỹ thuật |
| :--- | :---: | :---: | :--- |
| **Phân loại sự cố (Issue Triage P0-P3)** | `0.0` | `1.0` | Đòi hỏi tính nhất quán tuyệt đối, không được suy diễn ngẫu nhiên. |
| **Xuất JSON Schema / Pydantic** | `0.0` | `1.0` | Triệt tiêu nguy cơ sai cú pháp JSON và không bịa thêm trường lạ. |
| **Hỏi đáp nghiệp vụ nội bộ (RAG / Q&A)** | `0.2 - 0.3` | `1.0` | Câu văn tự nhiên, mượt mà nhưng vẫn bám sát 100% tài liệu gốc. |
| **Tóm tắt văn bản (Summarization)** | `0.3 - 0.5` | `1.0` | Đủ linh hoạt để nối câu trôi chảy mà không làm biến đổi ngữ nghĩa. |
| **Brainstorm / Sáng tạo nội dung** | `0.8 - 1.0` | `0.9` | Cần văn phong đa dạng, giàu hình ảnh và ý tưởng bất ngờ. |

---

#### F. Có thể điều khiển `temperature` và `top_p` trực tiếp trong Prompt không?
> **Câu trả lời dứt khoát về mặt kỹ thuật:** **KHÔNG THỂ.**  
> Nếu bạn viết vào prompt: *"Hãy tự set temperature = 0 và top_p = 0.85 để trả lời tôi nhé!"*, mô hình **hoàn toàn không làm được**.

```mermaid
graph TD
    subgraph Layer1["TẦNG 1: Ứng dụng & Prompt (Application / User)"]
        A["Prompt Text: '...Hãy set temp=0...'"]
    end

    subgraph Layer2["TẦNG 2: Mạng nơ-ron LLM (Weights)"]
        B["Đọc hiểu Prompt -> Chạy Attention -> Xuất ra Logits (Điểm thô)"]
    end

    subgraph Layer3["TẦNG 3: Bộ giải mã máy chủ (Inference / Decoding Engine)"]
        C{"ÁP DỤNG THAM SỐ SINH:<br/>1. Lọc theo top_p API config<br/>2. Chia điểm Softmax theo Temperature<br/>3. Bốc thăm chọn Token"}
        D["Bộ đếm max_tokens"]
    end

    A --> B
    B --> C
    C --> D
    D -->|"Token kết quả"| A
```

##### 1. Tại sao Prompt không điều khiển được tham số sinh?
* `temperature` và `top_p` **không nằm trong trọng số (weights)** của mô hình, mà nằm ở **Tầng 3 (Inference Engine)** bên ngoài mô hình.
* Inference Engine chỉ nhận tham số từ **cấu hình API Request (JSON payload)**, nó không "đọc nội dung văn bản" của prompt để tự cấu hình lại server.
* Khi bạn yêu cầu chỉnh tham số trong prompt, mô hình chỉ xem đó là văn bản thông thường và có thể lịch sự đáp lại: *"Vâng, tôi sẽ trả lời chính xác nhất..."*, nhưng bộ giải mã máy chủ vẫn bốc thăm theo tham số cấu hình của API.

##### 2. Ba nơi bạn thực sự nắm quyền kiểm soát:
1. **Trong mã nguồn gọi API (Application Code):**
   * *Google GenAI SDK:* `config=types.GenerateContentConfig(temperature=0.1, top_p=0.85)`
   * *OpenAI SDK:* `client.chat.completions.create(..., temperature=0.0, top_p=0.9)`
   * *LangChain:* `ChatOpenAI(temperature=0.0)`
2. **Trên giao diện Web / Playground:** Kéo các thanh trượt (Sliders) ở cột System Settings trên Google AI Studio hoặc OpenAI Playground.
3. **Trên Local LLM (Ollama, vLLM):** Khai báo trong `Modelfile`:
   ```dockerfile
   FROM llama3
   PARAMETER temperature 0.1
   PARAMETER top_p 0.85
   ```

##### 3. Kỹ thuật Prompt Engineering để "mô phỏng" hiệu ứng của Temperature:
Mặc dù không can thiệp được công thức toán học, bạn có thể dùng câu lệnh ép buộc hành vi (Behavioral constraints):
* **Mô phỏng $T \to 0$ (Chính xác, chống ảo giác):**
  > *"Chỉ sử dụng DUY NHẤT các thông tin có trong ngữ cảnh trên. Tuyệt đối KHÔNG suy đoán, không sáng tạo thêm. Nếu thông tin không được đề cập, bắt buộc phải trả lời: 'Không có dữ liệu'. Tuân thủ nghiêm ngặt schema đầu ra."*
* **Mô phỏng $T \to 1$ (Sáng tạo, đa dạng):**
  > *"Hãy đóng vai một nhà tư tưởng độc lập. Hãy đưa ra 5 góc nhìn hoàn toàn trái ngược với các định kiến thông thường. Sử dụng nhiều phép ẩn dụ táo bạo, mở rộng liên tưởng sang các lĩnh vực nghệ thuật và triết học."*

---

## PHẦN 2: PROMPT & CONTEXT ENGINEERING

### 1. Phân biệt hai khái niệm cốt lõi

```mermaid
flowchart LR
    subgraph PE["Prompt Engineering (Tập trung vào CÁCH HỎI)"]
        PE1["Thiết kế mô tả tác vụ"]
        PE2["Xây dựng Role / Instruction"]
        PE3["Ràng buộc & Định dạng đầu ra"]
    end

    subgraph CE["Context Engineering (Tập trung vào NẠP DỮ LIỆU GÌ)"]
        CE1["Chọn lọc dữ liệu từ RAG"]
        CE2["Cắt gọt lịch sử hội thoại"]
        CE3["Nạp kết quả tool / file liên quan"]
    end
```

> **Nguyên tắc vàng:** Đưa đúng và đủ thông tin quan trọng luôn hiệu quả hơn việc ném toàn bộ dữ liệu vào context.

---

### 2. Cấu trúc chuẩn của một Prompt (Sử dụng thẻ XML)
Để tránh việc model nhầm lẫn giữa lời chỉ thị của hệ thống và dữ liệu thô do người dùng nhập, bài giảng khuyến nghị cấu trúc hóa prompt bằng các thẻ XML:

```xml
<role>
Bạn là kỹ sư phụ trách phân loại sự cố hệ thống (Issue Triage).
</role>

<context>
Hệ thống API thanh toán trực tuyến đang chạy trên môi trường Production.
</context>

<task>
Phân loại mức độ nghiêm trọng của sự cố theo 4 cấp độ: P0, P1, P2, P3.
</task>

<constraints>
- Nếu dữ liệu trong issue không đủ kết luận, đánh dấu status là "insufficient_data".
- Tuyệt đối không tự suy đoán ngoài các chi tiết được cung cấp.
</constraints>

<input>
{issue_text}
</input>

<output>
Trả về mã severity (P0-P3) kèm theo lý do ngắn gọn (tối đa 2 câu).
</output>
```

---

### 3. In-context Learning & Chain of Thought (CoT)

```mermaid
graph LR
    ZS["Zero-shot<br/>(0 ví dụ)<br/>Token: Thấp nhất"] --> OS["One-shot<br/>(1 ví dụ)<br/>Token: Thấp"]
    OS --> FS["Few-shot<br/>(2-5 ví dụ)<br/>Token: Trung bình"]
    FS --> COT["Chain of Thought<br/>(Ví dụ + Lập luận bước)<br/>Token: Cao nhất"]
```

#### A. Few-shot Prompting & Đánh đổi (Trade-offs)
* **Bản chất:** Đưa vào prompt 2–5 cặp mẫu `(Input mẫu -> Output mẫu)` để model bắt chước quy luật phân loại và cấu trúc trả về mà không cần giải thích trừu tượng.
* **Đánh đổi:**
  * **Hữu ích khi:** Áp dụng hệ thống phân loại riêng của doanh nghiệp; minh họa các trường hợp ranh giới mập mờ (boundary cases) khó định nghĩa bằng lời.
  * **Phản tác dụng khi:** Làm phình to context window; gây thiên lệch nhãn (Bias - ví dụ đưa nhiều mẫu P0 thì model sẽ thiên về đoán P0); dùng ví dụ để ép JSON thay vì dùng Schema chuẩn.

#### B. Chain of Thought (CoT) - Kỹ thuật suy luận từng bước
* **Vấn đề của Zero-shot:** Khi gặp bài toán tính toán hoặc suy luận nhiều bước, nếu bắt LLM trả ngay đáp án cuối cùng, nó sẽ "đoán mò" token và tính nhẩm sai.
* **Cơ chế CoT:** Yêu cầu mô hình viết ra các bước trung gian trước. Đoạn văn bản suy luận này đóng vai trò như một **bảng nháp (scratchpad)** trong context để các token tính toán tiếp theo bám vào.
* **Xu hướng Reasoning Models:** Các dòng mô hình lý luận mới (OpenAI o1/o3, Gemini Thinking) đã tích hợp sẵn cơ chế suy luận ngầm bên trong, giảm bớt nhu cầu phải viết các câu thần chú thủ công như *"Hãy suy nghĩ từng bước một"*.

---

## PHẦN 3: STRUCTURED OUTPUT (ĐẦU RA CÓ CẤU TRÚC)

Đây là điều kiện tiên quyết để tích hợp LLM vào phần mềm tự động hóa.

```mermaid
flowchart TD
    subgraph Sai["Cách tiếp cận Mong manh (Brittle)"]
        M1["LLM trả Prose Text"] --> M2["Code dùng Regex / Substring"]
        M2 -->|Dễ gãy khi đổi format| M3["Lỗi ứng dụng (Runtime Crash)"]
    end

    subgraph Dung["Cách tiếp cận Chuẩn mực (Robust)"]
        C1["LLM ép theo JSON Schema"] --> C2["Dữ liệu có kiểu rõ ràng"]
        C2 -->|Ổn định 100%| C3["Code xử lý if-else an toàn"]
    end
```

---

### 1. JSON Schema & Pydantic trong Python

Để định nghĩa cấu trúc dữ liệu mong muốn, ta sử dụng **JSON Schema** hoặc khai báo thông qua **Pydantic**:

```python
from typing import Literal
from pydantic import BaseModel, Field

class IssueTriage(BaseModel):
    status: Literal["classified", "insufficient_data", "out_of_scope"]
    severity: Literal["P0", "P1", "P2", "P3"] | None = None
    component: str | None = None
    needs_urgent_response: bool = False
    reason: str = Field(description="Lý do ngắn gọn dựa trên dữ liệu issue")
```

#### Các từ khóa then chốt trong JSON Schema:
* **`properties`:** Danh sách và kiểu dữ liệu của các trường.
* **`required`:** Danh sách trường bắt buộc phải có, model không được phép bỏ sót.
* **`enum`:** Giới hạn tập giá trị hợp lệ (chống việc model tự tạo giá trị lạ).
* **`additionalProperties: false`:** Nghiêm cấm model tự ý sinh thêm trường ngoài schema.

---

### 2. Prompt-only vs Constrained Output (Ràng buộc cấp API)

* **Prompt-only:** Chỉ viết trong prompt: *"Hãy trả lời bằng JSON theo schema..."*.
  * **Rủi ro:** Model vẫn có thể tự ý thêm lời chào, bọc code fence ````json ... ````, thiếu trường, hoặc sinh sai kiểu dữ liệu.
* **Constrained Output:** Gửi schema trực tiếp vào tham số API (như `response_format` / `response_schema`).
  * **Cơ chế:** Nhà cung cấp can thiệp vào thuật toán lấy mẫu token (Grammar-guided decoding). Model bị chặn đứng về mặt toán học, **chỉ có thể sinh ra các token hợp lệ theo schema**.

> ⚠️ **Lưu ý cốt tử của bài giảng:**  
> **Schema chỉ kiểm tra tính hợp lệ về mặt CẤU TRÚC, không kiểm tra được tính đúng đắn về mặt NGỮ NGHĨA.**  
> *(Ví dụ: Model trả về `{"severity": "P0"}` là hoàn toàn hợp lệ theo schema, nhưng trên thực tế lỗi đó có đúng là P0 hay không thì schema không thể xác nhận được. Đó là lý do hệ thống vẫn cần validation nghiệp vụ ở phía Application).*

---

## PHẦN 4: FUNCTION CALLING & TOOL USE

Nếu **Structured Output** là việc model **trả về dữ liệu**, thì **Function Calling** là việc model **đề xuất một hành động có cấu trúc**.

```mermaid
sequenceDiagram
    autonumber
    participant App as "Application Code"
    participant LLM as "LLM Model"
    participant Ext as "Hệ thống bên ngoài (DB / API / Tool)"

    Note over App: Khai báo Tool Schema:<br/>name, description, arguments
    App->>LLM: Gửi Prompt + Tool Schemas
    Note over LLM: Phân tích yêu cầu & nhận thấy<br/>cần thông tin từ Tool
    LLM-->>App: Trả về Tool Call Request:<br/>{name: "get_component_owner", arguments: {"component": "payment"}}
    
    rect rgb(240, 248, 255)
    Note over App: ỨNG DỤNG TỰ THỰC THI (Model không tự chạy):<br/>Kiểm tra quyền, validate tham số
    App->>Ext: Gọi hàm nội bộ / API
    Ext-->>App: Kết quả: "team-checkout"
    end

    App->>LLM: Gửi Tool Result: {component: "payment", owner: "team-checkout"}
    Note over LLM: Tổng hợp thông tin từ Tool Result
    LLM-->>App: Câu trả lời cuối cùng (Final Response)
```

---

### 3 nguyên tắc bất di bất dịch của Tool Use:

1. **Model KHÔNG BAO GIỜ tự chạy code:** Model không thể truy cập database, không tự gọi REST API hay thực thi bash shell. Model chỉ tạo ra một đối tượng JSON mô tả lời đề nghị gọi hàm.
2. **Application nắm toàn quyền thực thi:** Mã nguồn ứng dụng của bạn là bên duy nhất quyết định có thực thi tool đó hay không, có quyền kiểm tra tính hợp lệ và áp đặt giới hạn an toàn (security/permissions).
3. **Đúng kiểu dữ liệu $\neq$ Đúng ý nghĩa:** Tham số truyền vào có thể đúng kiểu `string` (ví dụ `component: "payment-api-v2"`), nhưng component này có thể hoàn toàn không tồn tại trong hệ thống. Ứng dụng phải tự xử lý các trường hợp ngoại lệ này.

---

## PHẦN 5: BƯỚC CHUYỂN TIẾP SANG AI AGENT

### So sánh LLM-Powered App và AI Agent

```mermaid
flowchart TD
    subgraph AppFlow["1. LLM-Powered App (Mã nguồn định sẵn - Hard-coded)"]
        A1["Input"] --> A2["Gọi LLM"]
        A2 --> A3["Gọi Tool (nếu có)"]
        A3 --> A4["Kết thúc theo code định sẵn"]
    end

    subgraph AgentFlow["2. AI Agent (Vòng lặp tự trị - Autonomous Loop)"]
        B1["Goal (Mục tiêu lớn)"] --> B2["Observation (Quan sát môi trường)"]
        B2 --> B3["Reasoning / Action (Lập luận & Chọn tool)"]
        B3 --> B4{"Đã đạt Goal / Điều kiện dừng?"}
        B4 -- Chưa --> B2
        B4 -- Rồi --> B5["Hoàn thành nhiệm vụ"]
    end
```

* **LLM-Powered App (Hiện tại):** Luồng thực thi (control flow) là cố định do lập trình viên viết sẵn bằng code: nhận input $\rightarrow$ gọi model $\rightarrow$ chạy tool $\rightarrow$ trả kết quả.
* **AI Agent (Buổi tiếp theo):** Được trang bị một **Agent Loop**. Model tự nhận diện môi trường, tự quyết định gọi bao nhiêu công cụ, tự đánh giá xem đã đạt được mục tiêu hay chưa và chỉ dừng lại khi chạm điều kiện kết thúc (Termination Condition).

---

## 📝 Bảng tổng hợp thuật ngữ trọng tâm (Cheatsheet)

| Thuật ngữ | Ý nghĩa kỹ thuật cốt lõi |
| :--- | :--- |
| **Context Window** | Tổng dung lượng token cho phép trong 1 lần gọi API (gồm cả input + output). |
| **Lost in the middle** | Xu hướng bỏ quên chi tiết nằm ở giữa một context quá dài. |
| **In-context Learning** | Dạy mô hình thực hiện task mới thông qua ngữ cảnh prompt mà không đổi weights. |
| **Chain of Thought (CoT)** | Yêu cầu mô hình lập luận từng bước trung gian để hạn chế sai số tính toán. |
| **Constrained Output** | Ép cấu trúc đầu ra ở cấp độ thuật toán sinh token (Grammar-guided decoding). |
| **Function Calling** | Cơ chế model đề xuất hành động và tham số dưới dạng JSON để ứng dụng thực thi. |
| **Agent Loop** | Vòng lặp quan sát – suy luận – hành động nhiều bước cho phép AI hành động tự trị. |