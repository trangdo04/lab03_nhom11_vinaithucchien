# Individual Report: Lab 3 - Chatbot vs ReAct Agent

- **Student Name**: Nguyễn Thị Thanh Huyền
- **Student ID**: 2A202600211
- **Date**: 6/4/2026

---

## I. Technical Contribution (15 Points)

*Describe your specific contribution to the codebase (e.g., implemented a specific tool, fixed the parser, etc.).*
Implement tool general_searching dùng Tavily API để tìm kiếm thông tin y khoa tổng quát phục vụ cho agent trong quá trình reasoning
- **Modules Implementated**: `src/agent/tools/general_searching.py`
- **Code Highlights**: 
  - Khởi tạo Tavily client bằng API key từ environment variable để đảm bảo bảo mật: `self.client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))`
  - Query của người dùng được augment bằng medical context để tăng độ liên quan của kết quả tìm kiếm: `search_query = f"medical symptoms diseases treatment: {query}"` 
`response = self.client.search(query=search_query, search_depth="advanced", max_results=5)`
  - Chuẩn hoá dữ liệu trả về thành cấu trúc thống nhất để agent có thể sử dụng trong bước reasoning: `for r in results:` 
`extracted.append({"title": r.get("title", ""), "snippet": r.get("content", ""), "url": r.get("url", "")})`
  - Tool trả về structured JSON gồm status, message và danh sách nguồn tham khảo: `return {"status": "success", "tool": self.name, "query": query, "data": extracted, "message": f"Found {len(extracted)} medical search results."}`
- **Documentation**: Tool general_searching được dùng khi agent cần tra cứu kiến thức y khoa bên ngoài
  - Flow ngắn gọn: Agent nhận câu hỏi về triệu chứng/bệnh. Trong bước Thought, agent quyết định cần tìm thông tin → gọi tool general_searching. Tool dùng Tavily để tìm kiếm và trả về danh sách nguồn (title, snippet, url). Ở bước Observation, agent dùng kết quả này để suy luận và tạo câu trả lời cuối.

---

## II. Debugging Case Study (10 Points)

*Analyze a specific failure event you encountered during the lab using the logging system.*

- **Problem Description**: Agent không thể sử dụng các tool tìm kiếm (symptom, medicine, general). Mỗi lần agent gọi tool, hệ thống bị crash với lỗi AttributeError từ TavilyClient, khiến tool luôn trả về error và agent không thể truy cập dữ liệu web
- **Log Source**: 
```
General search failed: 'TavilyClient' object has no attribute 'search'
Traceback (most recent call last):
  File ".../general_searching.py", line 40, in execute
    response = self.client.search(
AttributeError: 'TavilyClient' object has no attribute 'search'

Symptom search failed: 'TavilyClient' object has no attribute 'search'
Medicine search failed: 'TavilyClient' object has no attribute 'search'
General search failed: 'TavilyClient' object has no attribute 'search'
```
- **Diagnosis**: Nguyên nhân không phải do LLM mà do tool implementation mismatch với Tavily SDK.
- **Solution**:
  - Cập nhật lại cách gọi Tavily theo đúng SDK:
  - Thay self.client.search(...) bằng method đúng của Tavily version đang dùng.
  - Thêm error handling và test riêng cho tool trước khi tích hợp vào agent.
  - Thêm integration test để verify tool hoạt động trước khi chạy agent.

Sau khi sửa, các tool mới có thể trả về dữ liệu thật và agent mới hoạt động đúng theo ReAct pipeline.
---

## III. Personal Insights: Chatbot vs ReAct (10 Points)

*Reflect on the reasoning capability difference.*

1.  **Reasoning**: How did the `Thought` block help the agent compared to a direct Chatbot answer?
- Thought block buộc agent phải tách quá trình suy nghĩ thành nhiều bước rõ ràng trước khi trả lời.
So với chatbot trả lời trực tiếp (one-shot), ReAct giúp:
  - Nhận diện khi nào thiếu kiến thức → chủ động gọi tool tìm kiếm. 
  - Chia bài toán thành các bước nhỏ: hiểu câu hỏi → quyết định tool → tổng hợp kết quả → trả lời. 
  - Giảm trả lời theo kiểu “đoán” vì agent có cơ chế kiểm tra lại bằng dữ liệu bên ngoài.

=> Kết quả: câu trả lời có lập luận có cấu trúc và có nguồn tham chiếu thay vì suy diễn thuần từ LLM.
2.  **Reliability**: In which cases did the Agent actually perform *worse* than the Chatbot?
- Trong một số tình huống:
  - Câu hỏi rất đơn giản (ví dụ: kiến thức phổ thông).
  → Chatbot trả lời ngay, còn agent mất thời gian gọi tool → overhead không cần thiết.
  - Tool trả về kết quả nhiễu / không liên quan.
  → Agent bị “nhiễu thông tin”, tổng hợp kém hơn chatbot.
  - Lỗi parsing hoặc tool failure.
  → ReAct pipeline phụ thuộc nhiều thành phần → dễ fail hơn hệ thống đơn giản.
  - Câu hỏi mơ hồ.
  → Agent có thể chọn sai tool → dẫn đến câu trả lời kém chất lượng.

=> Agent mạnh hơn về reasoning, nhưng độ ổn định phụ thuộc toolchain.
3.  **Observation**: How did the environment feedback (observations) influence the next steps?
- Observation đóng vai trò feedback loop cho vòng ReAct:
  - Sau khi gọi tool, agent nhận dữ liệu thực tế từ môi trường. 
  - Agent dùng observation để:
    - Xác nhận giả thuyết ban đầu đúng/sai 
    - Quyết định có cần gọi tool thêm hay không 
    - Tổng hợp thành câu trả lời cuối

- Observation giúp agent chuyển từ suy luận giả định → suy luận dựa trên bằng chứng.

=> Đây là điểm khác biệt cốt lõi:
- Chatbot = suy luận một bước. 
- ReAct Agent = suy luận lặp + phản hồi môi trường.

---

## IV. Future Improvements (5 Points)

*How would you scale this for a production-level AI agent system?*

- **Scalability**: 
  - Dùng async queue cho tool calls, tách tools thành microservices.
  - Lưu state vào DB (Redis/Postgres) để hỗ trợ nhiều user đồng thời.
  - Thêm tool registry để dễ mở rộng nhiều tools.
- **Safety**: 
  - Thêm Supervisor/Guardrail LLM để kiểm tra hallucination & prompt injection.
  - Phân quyền và log toàn bộ tool calls.
  - Validate input/output trước và sau mỗi vòng ReAct.
- **Performance**: 
  - Dùng Vector DB để chọn tool & lưu knowledge base.
  - Cache kết quả search và LLM responses.
  - Streaming response để giảm latency cảm nhận.

---

> [!NOTE]
> Submit this report by renaming it to `REPORT_[YOUR_NAME].md` and placing it in this folder.
