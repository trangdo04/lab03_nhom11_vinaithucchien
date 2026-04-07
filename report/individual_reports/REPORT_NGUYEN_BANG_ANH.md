# Individual Report: Lab 3 - Chatbot vs ReAct Agent

- **Student Name**: Nguyễn Bằng Anh
- **Student ID**: 2A2026000136
- **Date**: 07/04/2026

---

## I. Technical Contribution (15 Points)

In this project, I was responsible for **refining `EnhancedAgent` and the query tools** so the system could respond more naturally, more safely, and in a way that better matched the intended real-world use case.

- **Modules handled**:
  - `src/agent/enhance_agent.py`
  - `src/agent/tools/general_searching.py`
- **Key contributions**:
  - Added a safety filter inside `EnhancedAgent` to detect sensitive questions or requests for dangerous behavior, and reject them appropriately instead of continuing in the wrong reasoning path.
  - Adjusted the question-classification flow so medical questions are still handled, while truly dangerous content such as self-harm, violence, homemade drugs, or harmful instructions is blocked.
  - Refined the agent goal so it prioritizes a **possible disease name** or a small set of leading candidates instead of giving vague answers, which makes the response more relevant to the medical task.
  - Removed the `general_searching` tool call from `General Mode` to avoid returning raw JSON from the tool and switched to LLM-based natural language responses that are easier for users to read.
  - Updated `general_searching.py` so it actually serves general information instead of medical information, by changing the tool description and the query augmentation logic.
  - Kept the `Observation -> Predict/Re-question` flow in `EnhancedAgent`, while tuning the prompt so the agent is more likely to conclude quickly and less likely to loop with unnecessary follow-up questions.
- **Impact on the ReAct / Enhanced flow**:
  - The agent is safer because it blocks dangerous content before generating a response.
  - `General Mode` no longer depends on raw tool output, so the response is more natural and readable.
  - Medical questions are still processed, but the agent now tends to produce concise, diagnosis-oriented outputs instead of stretching the conversation.

---

## II. Debugging Case Study (10 Points)

- **Problem description**:  
During testing, one notable issue was that `General Mode` could return raw tool data, which made the answer look more like JSON or a result list than a readable paragraph. In addition, the agent needed a clear mechanism to block dangerous questions without affecting valid medical questions.
- **Logs / observations**:  
Test runs showed that when using `general_searching`, the output tended to include structured API data that was not suitable to present directly to the user. At the same time, for sensitive prompts, relying only on medical classification could accidentally send the agent into an unsafe response path.
- **Root cause analysis**:  
The issue came from two factors:
  - `General Mode` called the search tool directly and received structured output without an LLM grounding step.
  - The initial safety filter did not clearly separate valid medical questions from dangerous requests.
- **Solutions implemented**:
  1. Removed `general_searching` from `General Mode` and switched to direct LLM-based responses.
  2. Added `_is_sensitive_or_harmful()` with a condition based on whether the question is medical.
  3. Blocked only requests that ask for dangerous behavior, while allowing medical questions to continue through the normal medical flow.
  4. Tuned the `EnhancedAgent` prompt to favor concise, evidence-based conclusions instead of repeated follow-up questions.
- **Result after the fix**:  
The agent now responds more smoothly, avoids raw tool output, reduces unnecessary back-and-forth, and still remains safe when dealing with harmful content.

---

## III. Personal Reflection: Chatbot vs ReAct (10 Points)

Through Lab 3, I found that the biggest difference between a regular chatbot and a ReAct/Enhanced Agent is **control over the response process**. A chatbot responds directly, so it is fast, but it can easily go off track when the question is difficult or sensitive. In contrast, a ReAct Agent separates thinking, action, and observation, which makes the overall process easier to control.

For a medical task, the important part is not asking too many questions, but asking the right ones and then quickly moving toward a careful conclusion. After tuning `EnhancedAgent`, I found that this approach is better when the goal is to provide a possible disease name or an initial direction, because it tends to conclude earlier instead of prolonging the conversation. However, I also noticed that if the tool or prompt is not well standardized, the agent can become slower or sound less natural than a simple chatbot.

From practical experience, Observation is the most important part because it turns reasoning into evidence-based reasoning. When the observation is good, the agent responds more confidently; when the observation is weak or incomplete, the agent should stop or ask a selective follow-up question. I learned that for medical systems, **safety, clarity, and evidence** matter more than answering too quickly.

---

## IV. Future Improvements (5 Points)

In the future, I want to continue improving the system in three main directions:

- **Scalability:**  
Move tool calls to an asynchronous model, add caching for common queries, and make the pipeline between agents more standardized.
- **Safety:**  
Add stronger guardrails to detect prompt injection, dangerous content, and questions that go beyond medical advice.
- **Performance:**  
Reduce unnecessary follow-up questions, optimize the prompt so the agent can conclude faster, and track more detailed telemetry for each reasoning step.

Overall, the development direction I prioritize is building the agent with the principle: **safety first, clarity first, then speed and experience optimization**.

---

> [!NOTE]
> Submit this report by renaming the file to `REPORT_[YOUR_NAME].md` and placing it in this folder.
