# **Báo cáo Nhóm: Lab 3 - Hệ thống Agentic chuẩn Production (Sẵn sàng triển khai)**

- **Tên nhóm**: Nhóm 11
- **Thành viên:**
  - Nguyễn Bằng Anh - 2A202600136
  - Đỗ Thị Thùy Trang - 2A202600041
  - Bùi Trọng Anh - 2A202600010
  - Nguyễn Thị Thanh Huyền - 2A202600211
- **Ngày triển khai**: [2026-04-06]

---

## **1. Tóm tắt dự án (Executive Summary)**

Dự án xây dựng một **Medical Agent** theo hướng **Agentic AI** nhằm hỗ trợ người dùng tra cứu thông tin sức khỏe an toàn và có căn cứ hơn chatbot thông thường. Hệ thống được thiết kế với 2 lớp tác tử: **ReActAgent** thực thi vòng lặp *Thought - Action - Observation* để chủ động gọi công cụ tìm kiếm, và **EnhancedAgent** theo kiến trúc node-based, có khả năng phân loại câu hỏi y tế, tổng hợp quan sát từ nhiều công cụ, quyết định trả lời hoặc hỏi làm rõ khi dữ liệu chưa đủ. Nhờ đó, agent giảm xu hướng trả lời cảm tính, tăng tính minh bạch trong quá trình suy luận và phù hợp hơn cho các truy vấn y khoa nhiều bước.

Về triển khai kỹ thuật, dự án chuẩn hóa tầng mô hình qua `LLMProvider` (hỗ trợ **Gemini / OpenAI / Local model**), tích hợp bộ công cụ y tế (`symptom_searching`, `medicine_searching`, `general_searching`) dựa trên Tavily để lấy dữ liệu thời gian thực, đồng thời bổ sung lưu lịch sử hội thoại và logging có cấu trúc JSON phục vụ theo dõi vận hành. Ứng dụng có cả giao diện terminal (`demo.py`) và giao diện so sánh song song 2 agent trên Streamlit (`streamlit_app.py`), giúp nhóm kiểm thử nhanh chất lượng phản hồi và phân tích sai lỗi.

- **Kết quả then chốt**: *Agent thể hiện tốt hơn chatbot cơ bản trong các câu hỏi cần tra cứu đa nguồn, nhờ cơ chế gọi tool có kiểm soát và bước đánh giá “đủ thông tin hay cần hỏi thêm”.*

---

## **2. Kiến trúc hệ thống & Công cụ (Tooling)**

Hệ thống được thiết kế theo kiến trúc mô-đun, tách rõ 4 lớp chính: **(1) lớp giao diện người dùng**, **(2) lớp điều phối agent**, **(3) lớp mô hình ngôn ngữ (LLM Provider)** và **(4) lớp công cụ tìm kiếm y tế**.  
Về giao diện, dự án hỗ trợ cả terminal (`demo.py`) và web app so sánh song song 2 agent (`streamlit_app.py`).  
Về điều phối, nhóm triển khai hai agent: `ReActAgent` (vòng lặp Thought-Action-Observation) và `EnhancedAgent` (node-based flow: phân loại câu hỏi -> quan sát tool -> dự đoán hoặc hỏi làm rõ).  
Các công cụ y tế dùng chung interface `MedicalTool`, giúp mở rộng dễ dàng mà không phụ thuộc cụ thể vào một tool hay API duy nhất.

### **2.1 Triển khai vòng lặp ReAct**

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

### **2.2 Danh mục công cụ (Tool Inventory)**


|                      |                       |                                                                                 |
| -------------------- | --------------------- | ------------------------------------------------------------------------------- |
| **Tên công cụ**      | **Định dạng đầu vào** | **Mục đích sử dụng**                                                            |
| `symptom_searching`  | `string`              | Tìm thông tin triệu chứng, nguyên nhân, hướng xử trí ban đầu từ nguồn web y tế. |
| `medicine_searching` | `string`              | Tra cứu công dụng, liều dùng tham khảo, tác dụng phụ và lưu ý liên quan thuốc.  |
| `general_searching`  | `string`              | Tìm kiến thức y tế phổ thông, thông tin điều trị/chăm sóc sức khỏe tổng quát.   |
| `tavily_client`      | `string`              | Adapter truy vấn Tavily API, chuẩn hóa phản hồi cho các tool ở trên.            |


### **2.3 Các mô hình LLM sử dụng**

- **Mô hình chính (Primary)**: [Ví dụ: GPT-4o]
- **Mô hình dự phòng (Backup)**: [Ví dụ: Gemini 1.5 Flash]

---

## **3. Chỉ số đo lường & Hiệu năng (Telemetry Dashboard)**

*Phân tích các chỉ số vận hành được thu thập trong đợt kiểm thử cuối cùng.*

- **Độ trễ trung bình (Average Latency - P50)**: ~5954ms
- **Độ trễ tối đa (Max Latency - P99)**: ~54482ms
- **Số lượng Token trung bình/tác vụ**: ~1000 token
- **Tổng chi phí bộ kiểm thử (Total Cost)**: Không có vì dùng mô hình miễn phí

---

## **4. Phân tích nguyên nhân gốc rễ (RCA) - Lịch sử lỗi**



---

## **5. Thử nghiệm thay đổi (Ablation Studies & Experiments)**

### **Thử nghiệm 1: Prompt v1 so với Prompt v2**

- **Thay đổi**: [Ví dụ: Thêm dòng "Luôn kiểm tra kỹ tham số công cụ trước khi gọi".]
- **Kết quả**: Giảm [Ví dụ: 30%] các lỗi gọi công cụ sai định dạng.

### **Thử nghiệm 2 (Bonus): Chatbot vs Agent**


|                  |                     |                   |                 |
| ---------------- | ------------------- | ----------------- | --------------- |
| **Trường hợp**   | **Kết quả Chatbot** | **Kết quả Agent** | **Người thắng** |
| Câu hỏi đơn giản | Đúng                | Đúng              | Hòa             |
| Truy vấn đa bước | Bị ảo giác          | Đúng              | **Agent**       |


---

## **6. Đánh giá mức độ sẵn sàng triển khai (Production Readiness)**

*Các yếu tố cần cân nhắc khi đưa hệ thống này vào môi trường thực tế.*

- **Bảo mật (Security)**: [Ví dụ: Kiểm soát dữ liệu đầu vào (sanitization) cho các tham số công cụ.]
- **Rào chắn (Guardrails)**: [Ví dụ: Giới hạn tối đa 5 vòng lặp để tránh phát sinh chi phí vô tận.]
- **Khả năng mở rộng (Scaling)**: [Ví dụ: Chuyển sang sử dụng LangGraph để quản lý các luồng rẽ nhánh phức tạp hơn.]

---

