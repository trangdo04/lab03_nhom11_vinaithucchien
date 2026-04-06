# Báo cáo Cá nhân: Lab 3 - Chatbot so với ReAct Agent

- **Họ và tên sinh viên**: Bùi Trọng Anh
- **Mã số sinh viên**: 2A202600010
- **Ngày thực hiện**: 06/04/2026

---

## I. Đóng góp Kỹ thuật (15 Điểm)

Trong project này, tôi phụ trách **hoàn thiện tool** `medicine_searching.py` để tăng độ ổn định khi truy vấn thông tin thuốc và tích hợp tốt hơn vào vòng lặp ReAct.

- **Module phụ trách**: `src/agent/tools/medicine_searching.py`
- **Đóng góp chính**:
  - Chuẩn hóa lớp `MedicineSearchingTool` kế thừa `MedicalTool` với định danh `medicine_searching` và mô tả rõ mục đích sử dụng.
  - Thêm cơ chế kiểm tra đầu vào (`query`) và chuẩn hóa dữ liệu truy vấn trước khi gọi API.
  - Tích hợp Tavily qua `TavilyClient` và chuyển từ cách gọi cũ sang `client.query(...)` để đồng bộ interface hiện tại.
  - Xử lý phản hồi linh hoạt cho cả trường hợp `data` là `list` hoặc object đơn, sau đó chuẩn hóa về danh sách kết quả đồng nhất.
  - Chuẩn hóa output theo cấu trúc thống nhất (`status`, `tool`, `query`, `data`, `message`) để agent dễ parse thành Observation.
  - Giới hạn độ dài nội dung `content` (cắt tối đa 1000 ký tự) để kiểm soát token và tránh prompt quá dài.
  - Bổ sung logging theo vòng đời tool với các event `TOOL_START` và `TOOL_RESULT` (success/error), giúp theo dõi hiệu năng và truy vết lỗi rõ ràng.
  - Tăng khả năng chịu lỗi với các nhánh exception riêng (`ValueError`, `RuntimeError`, và exception tổng quát), đảm bảo tool không làm vỡ luồng của agent.
- **Tác động tới ReAct loop**:
  - Tool trả dữ liệu sạch, thống nhất, giúp `ReActAgent` tạo Observation ổn định hơn.
  - Khi lỗi (thiếu API key, query rỗng, lỗi Tavily), tool phản hồi có cấu trúc thay vì crash, từ đó agent vẫn có thể fallback và trả lời an toàn.

---

## II. Phân tích lỗi (Debugging Case Study) (10 Điểm)

- **Mô tả vấn đề**:  
Trong quá trình test `medicine_searching`, em gặp 2 lỗi chính:  
(1) kết quả search trả về **không đúng trọng tâm câu hỏi** của người dùng,  
(2) nội dung trả về **quá dài**, làm phản hồi của agent bị loãng và tốn token.
- **Nguồn log**:  
Các phiên test trong `logs/2026-04-06.log` cho thấy tool vẫn chạy nhưng chất lượng nội dung không ổn định; một số câu trả lời dài bất thường dù câu hỏi ngắn.
- **Chẩn đoán nguyên nhân**:  
Nguyên nhân đến từ lớp chuẩn hóa dữ liệu trong tool:
  - Query gửi đi chưa được chuẩn hóa đủ tốt nên Tavily có thể trả về kết quả rộng, ít liên quan.
  - Dữ liệu trả về từ API có thể ở nhiều dạng (list/object/string), nếu không normalize kỹ thì dễ đưa cả phần dư thừa vào response.
  - Chưa có giới hạn độ dài nội dung từng kết quả nên output có thể phình to.
- **Giải pháp đã thực hiện**:
  1. Chuẩn hóa query đầu vào (trim, làm rõ intent tìm thuốc).
  2. Chuẩn hóa response từ Tavily về một cấu trúc thống nhất để xử lý ổn định.
  3. Lọc và định dạng lại các trường quan trọng (`title`, `url`, `content`).
  4. **Giới hạn độ dài** `content` (cắt ngắn) để tránh trả về quá dài và giảm token.
  5. Bổ sung logging `TOOL_START/TOOL_RESULT` để theo dõi số lượng kết quả và trạng thái thành công/thất bại.
- **Kết quả sau khi sửa**:  
Kết quả tìm kiếm bám sát nội dung câu hỏi hơn, phản hồi ngắn gọn hơn, dễ dùng hơn cho vòng lặp ReAct và giảm tình trạng câu trả lời dài không cần thiết.

---

## III. Góc nhìn cá nhân: Chatbot so với ReAct (10 Điểm)

Qua quá trình làm Lab 3, em nhận thấy điểm khác biệt lớn nhất giữa Chatbot thường và ReAct Agent là **khả năng ra quyết định có căn cứ**. Chatbot thường trả lời trực tiếp dựa trên tri thức đã học nên nhanh, nhưng dễ “ảo giác” khi gặp câu hỏi y tế cần dữ kiện mới. Ngược lại, ReAct Agent có chuỗi Thought -> Action -> Observation, nên có thể chủ động gọi tool để kiểm chứng thông tin trước khi kết luận.

Về độ tin cậy, ReAct Agent mạnh hơn ở các truy vấn nhiều bước (ví dụ vừa hỏi triệu chứng vừa hỏi thuốc), nhưng cũng bộc lộ điểm yếu khi tầng tool gặp lỗi API hoặc lỗi mạng. Khi đó, câu trả lời có thể bị chậm, hoặc phải fallback an toàn. Điều này cho thấy chất lượng Agent không chỉ phụ thuộc vào model mà còn phụ thuộc mạnh vào “độ khỏe” của hệ sinh thái công cụ.

Từ trải nghiệm cá nhân, Observation là thành phần quan trọng nhất vì nó tạo vòng phản hồi thực tế cho agent. Khi observation rõ ràng, agent trả lời chắc chắn và đúng ngữ cảnh hơn. Khi observation lỗi hoặc thiếu, agent nên hỏi lại người dùng thay vì trả lời chắc như đúng rồi. Em rút ra rằng với bài toán y tế, **“trả lời thận trọng nhưng có căn cứ”** giá trị hơn “trả lời nhanh”.

---

## IV. Cải tiến trong tương lai (5 Điểm)

Trong tương lai, để hệ thống đạt mức production, em đề xuất 3 hướng cải tiến chính:

- **Khả năng mở rộng (Scalability):**  
Tách các lệnh gọi tool sang cơ chế bất đồng bộ và có retry policy; bổ sung cache cho truy vấn phổ biến để giảm tải và giảm độ trễ.
- **An toàn (Safety):**  
Thiết kế thêm lớp guardrail cho nội dung y tế (lọc mức rủi ro, bắt buộc khuyến nghị gặp bác sĩ ở tình huống nghiêm trọng, kiểm tra phát ngôn vượt phạm vi tư vấn).
- **Hiệu năng (Performance):**  
Ghi telemetry chi tiết hơn (token/latency theo từng bước Thought-Action), tối ưu prompt để giảm số vòng lặp, và áp dụng chiến lược chọn model theo độ khó câu hỏi để cân bằng chi phí - chất lượng.

Tổng kết lại, định hướng cải tiến của em là xây dựng agent theo tiêu chí: **ổn định trước, an toàn trước, rồi mới tối ưu tốc độ và chi phí**.

---

> [!NOTE] Nộp báo cáo này bằng cách đổi tên file thành `REPORT_[TEN_CUA_BAN].md` và đặt vào thư mục này.

