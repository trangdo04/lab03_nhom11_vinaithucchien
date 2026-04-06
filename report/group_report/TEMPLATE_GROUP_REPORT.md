# Báo cáo Nhóm: Lab 3 - Hệ thống Agentic chuẩn Production (Sẵn sàng triển khai)

- **Tên nhóm**: Nhóm 11
- **Thành viên:**
  - Nguyễn Bằng Anh - 2A2026000136
  - Đỗ Thị Thùy Trang - 2A202600041
  - Bùi Trọng Anh - 2A202600010
  - Nguyễn Thị Thanh Huyền - 2A202600211
- **Ngày triển khai**: [2026-04-06]

---

## 1. Tóm tắt dự án (Executive Summary)

Dự án xây dựng một **Medical Agent** theo hướng **Agentic AI** nhằm hỗ trợ người dùng tra cứu thông tin sức khỏe an toàn và có căn cứ hơn chatbot thông thường. Hệ thống được thiết kế với 2 lớp tác tử: **ReActAgent** thực thi vòng lặp *Thought - Action - Observation* để chủ động gọi công cụ tìm kiếm, và **EnhancedAgent** theo kiến trúc node-based, có khả năng phân loại câu hỏi y tế, tổng hợp quan sát từ nhiều công cụ, quyết định trả lời hoặc hỏi làm rõ khi dữ liệu chưa đủ. Nhờ đó, agent giảm xu hướng trả lời cảm tính, tăng tính minh bạch trong quá trình suy luận và phù hợp hơn cho các truy vấn y khoa nhiều bước.

Về triển khai kỹ thuật, dự án chuẩn hóa tầng mô hình qua `LLMProvider` (hỗ trợ **Gemini / OpenAI / Local model**), tích hợp bộ công cụ y tế (`symptom_searching`, `medicine_searching`, `general_searching`) dựa trên Tavily để lấy dữ liệu thời gian thực, đồng thời bổ sung lưu lịch sử hội thoại và logging có cấu trúc JSON phục vụ theo dõi vận hành. Ứng dụng có cả giao diện terminal (`demo.py`) và giao diện so sánh song song 2 agent trên Streamlit (`streamlit_app.py`), giúp nhóm kiểm thử nhanh chất lượng phản hồi và phân tích sai lỗi.

- **Kết quả then chốt**: *Agent thể hiện tốt hơn chatbot cơ bản trong các câu hỏi cần tra cứu đa nguồn, nhờ cơ chế gọi tool có kiểm soát và bước đánh giá “đủ thông tin hay cần hỏi thêm”.*

---

## 2. Kiến trúc hệ thống & Công cụ (Tooling)

Hệ thống được thiết kế theo kiến trúc mô-đun, tách rõ 4 lớp chính: **(1) lớp giao diện người dùng**, **(2) lớp điều phối agent**, **(3) lớp mô hình ngôn ngữ (LLM Provider)** và **(4) lớp công cụ tìm kiếm y tế**.  
Về giao diện, dự án hỗ trợ cả terminal (`demo.py`) và web app so sánh song song 2 agent (`streamlit_app.py`).  
Về điều phối, nhóm triển khai hai agent: `ReActAgent` (vòng lặp Thought-Action-Observation) và `EnhancedAgent` (node-based flow: phân loại câu hỏi -> quan sát tool -> dự đoán hoặc hỏi làm rõ).  
Các công cụ y tế dùng chung interface `MedicalTool`, giúp mở rộng dễ dàng mà không phụ thuộc cụ thể vào một tool hay API duy nhất.

### 2.1 Triển khai vòng lặp ReAct

Trong `ReActAgent`, luồng xử lý được thực hiện theo chu kỳ:

1. Nhận câu hỏi người dùng, nạp `system prompt` + ngữ cảnh hội thoại từ `ConversationHistory`.
2. Gọi LLM sinh phản hồi trung gian.
3. Parse hành động theo mẫu `Action: tool_name(argument)`.
4. Thực thi tool tương ứng và lấy `Observation`.
5. Bổ sung Observation vào prompt để LLM suy luận tiếp.
6. Dừng khi tìm được `Final Answer` hoặc đạt `max_steps` (mặc định 5 vòng).

Cơ chế này giúp agent:

- Chủ động truy xuất tri thức thời gian thực thay vì trả lời thuần từ tham số mô hình.
- Tăng khả năng xử lý câu hỏi đa bước (triệu chứng + thuốc + khuyến nghị).
- Có điểm kiểm soát vòng lặp để tránh chi phí/vòng lặp vô hạn.

Ngoài ra, `EnhancedAgent` bổ sung flow nâng cao:

- Phân loại câu hỏi y tế / không y tế.
- Nếu y tế: gọi đồng thời nhiều tool (`symptom`, `medicine`, `general`) để tạo tập quan sát.
- Đánh giá “đã đủ thông tin chưa”; nếu chưa đủ thì sinh câu hỏi follow-up thay vì trả lời thiếu căn cứ.

### 2.2 Danh mục công cụ (Tool Inventory)


|                      |                       |                                                                                 |
| -------------------- | --------------------- | ------------------------------------------------------------------------------- |
| **Tên công cụ**      | **Định dạng đầu vào** | **Mục đích sử dụng**                                                            |
| `symptom_searching`  | `string`              | Tìm thông tin triệu chứng, nguyên nhân, hướng xử trí ban đầu từ nguồn web y tế. |
| `medicine_searching` | `string`              | Tra cứu công dụng, liều dùng tham khảo, tác dụng phụ và lưu ý liên quan thuốc.  |
| `general_searching`  | `string`              | Tìm kiến thức y tế phổ thông, thông tin điều trị/chăm sóc sức khỏe tổng quát.   |
| `tavily_client`      | `string`              | Adapter truy vấn Tavily API, chuẩn hóa phản hồi cho các tool ở trên.            |


### 2.3 Các mô hình LLM sử dụng

- **Mô hình chính (Primary)**: [Ví dụ: GPT-4o]
- **Mô hình dự phòng (Backup)**: [Ví dụ: Gemini 1.5 Flash]

---

## 3. Chỉ số đo lường & Hiệu năng (Telemetry Dashboard)

*Phân tích các chỉ số vận hành được thu thập trong đợt kiểm thử cuối cùng.*

- **Độ trễ trung bình (Average Latency - P50)**: [Ví dụ: 1200ms]
- **Độ trễ tối đa (Max Latency - P99)**: [Ví dụ: 4500ms]
- **Số lượng Token trung bình/tác vụ**: [Ví dụ: 350 tokens]
- **Tổng chi phí bộ kiểm thử (Total Cost)**: [Ví dụ: $0.05]

---

## 4. Phân tích nguyên nhân gốc rễ (RCA) - Lịch sử lỗi

Dưới đây là nội dung bạn có thể dán cho **Phần 4 - Phân tích nguyên nhân gốc rễ (RCA)**:

---

## **4. Phân tích nguyên nhân gốc rễ (RCA) - Lịch sử lỗi**

Trong quá trình kiểm thử, nhóm ghi nhận các lỗi tập trung ở 3 nhóm chính: **(1) lỗi gọi công cụ do định dạng phản hồi LLM không ổn định**, **(2) lỗi dữ liệu ngoài do phụ thuộc API tìm kiếm**, và **(3) lỗi chất lượng câu trả lời khi thông tin đầu vào chưa đủ**.  
Dù hệ thống đã có guardrails như `max_steps`, fallback message và chuẩn hóa output tool, một số tình huống vẫn gây suy giảm độ chính xác hoặc trải nghiệm người dùng.

### **Case Study 1: LLM không sinh đúng định dạng** `Action`

- **Đầu vào (Input)**: “Tôi bị đau đầu 2 ngày nay, có nên uống paracetamol không?”
- **Quan sát (Observation)**: Agent đôi lúc trả lời mô tả tự do mà không có dòng `Action: tool_name(argument)`, khiến vòng ReAct không gọi được tool ở bước đó.
- **Nguyên nhân gốc rễ**: Parser trong `ReActAgent` dùng regex chặt theo mẫu `Action: ...`; khi LLM lệch format, agent không trích xuất được hành động.
- **Tác động**: Giảm khả năng truy xuất dữ liệu thời gian thực; câu trả lời có thể thiên về suy đoán.
- **Hướng khắc phục**:
  - Tăng ràng buộc prompt với few-shot đúng format.
  - Bổ sung parser dự phòng cho nhiều biến thể cú pháp.
  - Thêm cơ chế “reprompt yêu cầu xuất Action hợp lệ” trước khi bỏ qua bước tool.

### **Case Study 2: Phụ thuộc Tavily API (key/endpoint/network)**

- **Đầu vào (Input)**: Câu hỏi y tế cần tra cứu nguồn ngoài.
- **Quan sát (Observation)**: Tool trả về lỗi như thiếu `TAVILY_API_KEY`, lỗi endpoint hoặc request fail.
- **Nguyên nhân gốc rễ**: Hệ thống phụ thuộc dịch vụ bên ngoài; lỗi cấu hình môi trường hoặc lỗi mạng sẽ làm gián đoạn luồng quan sát.
- **Tác động**: Agent không lấy được dữ liệu mới, làm giảm chất lượng câu trả lời ở các truy vấn cần bằng chứng.
- **Hướng khắc phục**:
  - Kiểm tra health/config khi khởi động (preflight checks).
  - Bổ sung fallback provider/tầng cache cho truy vấn phổ biến.
  - Gắn mã lỗi chuẩn để dễ theo dõi trên telemetry dashboard.

### **Case Study 3: Trả lời sớm khi thông tin bệnh cảnh chưa đủ**

- **Đầu vào (Input)**: “Tôi đau ngực.”
- **Quan sát (Observation)**: Trong vài trường hợp, phản hồi còn chung chung; thiếu bước hỏi sâu về thời gian, mức độ, triệu chứng kèm theo.
- **Nguyên nhân gốc rễ**: Dữ liệu truy vấn ban đầu quá ngắn; nếu không kích hoạt đúng nhánh hỏi lại (re-question), chất lượng tư vấn giảm.
- **Tác động**: Câu trả lời chưa đủ hữu ích để người dùng ra quyết định tiếp theo.
- **Hướng khắc phục**:
  - Ưu tiên chiến lược hỏi lại khi tín hiệu rủi ro cao hoặc dữ liệu mơ hồ.
  - Chuẩn hóa bộ câu hỏi follow-up theo mẫu lâm sàng tối thiểu.
  - Tăng test case cho các input ngắn, thiếu ngữ cảnh.

### **Tổng kết RCA**

Các lỗi hiện tại **không chủ yếu đến từ thuật toán lõi**, mà đến từ tính bất định của đầu ra LLM và mức độ tin cậy của dịch vụ bên ngoài.  
Do đó, hướng cải tiến ưu tiên là: **(1) siết chuẩn giao thức LLM-tool**, **(2) tăng khả năng chịu lỗi cho lớp tích hợp API**, và **(3) mở rộng bộ test tình huống thiếu dữ kiện**. Điều này giúp agent ổn định hơn khi tiến gần môi trường production.

---

## 5. Thử nghiệm thay đổi (Ablation Studies & Experiments)

### Thử nghiệm 1: Prompt v1 so với Prompt v2

- **Thay đổi**: [Ví dụ: Thêm dòng "Luôn kiểm tra kỹ tham số công cụ trước khi gọi".]
- **Kết quả**: Giảm [Ví dụ: 30%] các lỗi gọi công cụ sai định dạng.

### Thử nghiệm 2 (Bonus): Chatbot vs Agent


|                  |                     |                   |                 |
| ---------------- | ------------------- | ----------------- | --------------- |
| **Trường hợp**   | **Kết quả Chatbot** | **Kết quả Agent** | **Người thắng** |
| Câu hỏi đơn giản | Đúng                | Đúng              | Hòa             |
| Truy vấn đa bước | Bị ảo giác          | Đúng              | **Agent**       |


---

## 6. Đánh giá mức độ sẵn sàng triển khai (Production Readiness)

*Các yếu tố cần cân nhắc khi đưa hệ thống này vào môi trường thực tế.*

- **Bảo mật (Security)**: [Ví dụ: Kiểm soát dữ liệu đầu vào (sanitization) cho các tham số công cụ.]
- **Rào chắn (Guardrails)**: [Ví dụ: Giới hạn tối đa 5 vòng lặp để tránh phát sinh chi phí vô tận.]
- **Khả năng mở rộng (Scaling)**: [Ví dụ: Chuyển sang sử dụng LangGraph để quản lý các luồng rẽ nhánh phức tạp hơn.]

---

> [!NOTE]
>
> Nộp báo cáo này bằng cách đổi tên file thành `GROUP_REPORT_[TEN_NHOM].md` và đặt vào thư mục này.

