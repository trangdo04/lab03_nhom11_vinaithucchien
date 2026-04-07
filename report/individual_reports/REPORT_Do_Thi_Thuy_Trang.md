# Individual Report: Lab 3 - Chatbot vs ReAct Agent

- **Student Name**: Đỗ Thị Thùy Trang
- **Student ID**: 2A202600041
- **Date**: 06/04/2026

---

## I. Technical Contribution (15 Points)

*Describe your specific contribution to the codebase (e.g., implemented a specific tool, fixed the parser, etc.).*

- **Modules Implementated**: `src/agent/tools/symptom_searching.py`
- **Code Highlights**: 
  ```python
  class SymptomSearchingTool(MedicalTool):
      """Công cụ tìm kiếm thông tin triệu chứng bằng Tavily."""
      
          # ... (other implementation details)
  ```
- **Documentation**: Em đã phát triển tool `symptom_searching.py` để tích hợp vào ReAct loop, hỗ trợ tìm kiếm thông tin triệu chứng bệnh từ Tavily API. Tool này xử lý query, chuẩn hóa kết quả và trả về dữ liệu có cấu trúc để agent sử dụng trong quá trình reasoning.
---

## II. Debugging Case Study (10 Points)

*Analyze a specific failure event you encountered during the lab using the logging system.*

- **Problem Description**: Trong quá trình thử nghiệm `symptom_searching`, em nhận thấy tool gặp 2 lỗi. Đầu tiên, khi query rỗng, dẫn đến phản hồi không hợp lệ. Tiếp theo là API trả về quá nhiều thông tin thô không cần thiết làm agent bị nhiễu thông tin. 
- **Log Source**: `logs/2026-04-06.log`
  ```
  ERROR: Yêu cầu tìm kiếm không được để trống. Tool: symptom_searching, Query: ""
  ```
- **Diagnosis**: Lỗi xảy ra do thiếu kiểm tra đầu vào trong tool, dẫn đến việc gửi query rỗng tới Tavily API. Với lõi thứ 2, do API mặc định trả về raw data bao gồm nhiều thông tin search được mà chưa có code xử lý những raw data này.
- **Solution**: Thêm kiểm tra query đầu vào trong `symptom_searching.py` để từ chối các truy vấn không hợp lệ trước khi gọi API. Về lỗi API trả về nhiều thông tin thì em chỉ chọn trả về những thông tin cần thiết như url và content chứ không trả về toàn bộ để đưa vào LLM trong những bước tiếp theo.

---

## III. Personal Insights: Chatbot vs ReAct (10 Points)

*Reflect on the reasoning capability difference.*

1.  **Reasoning**: Thought block giúp agent suy nghĩ từng bước, phân tích vấn đề trước khi hành động, làm cho câu trả lời chính xác và có lý lẽ hơn so với chatbot trực tiếp trả lời dựa trên kiến thức tĩnh.
2.  **Reliability**: Agent có thể hoạt động kém hơn chatbot khi tool trả về lỗi hoặc thông tin không liên quan, dẫn đến vòng lặp vô hạn, trong khi chatbot có thể trả lời dựa trên training data.
3.  **Observation**: Feedback từ observations giúp agent điều chỉnh hành động tiếp theo, ví dụ nếu tool trả về kết quả tốt, agent tiếp tục; nếu lỗi, agent có thể thử lại hoặc chọn tool khác.

---

## IV. Future Improvements (5 Points)

*How would you scale this for a production-level AI agent system?*

- **Scalability**: Sử dụng asynchronous queue cho tool calls để xử lý nhiều requests đồng thời, và caching kết quả tìm kiếm để giảm latency.
- **Safety**: Implement một 'Supervisor' LLM để audit các actions của agent trước khi thực thi, đảm bảo không có hành động nguy hiểm.
- **Performance**: Tích hợp Vector DB để retrieval tool nhanh chóng trong hệ thống nhiều tool, và sử dụng model lớn hơn cho reasoning tốt hơn.

---

> [!NOTE]
> Submit this report by renaming it to `REPORT_[YOUR_NAME].md` and placing it in this folder.
