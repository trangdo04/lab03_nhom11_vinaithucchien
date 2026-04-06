import streamlit as st
from src.agent.agent import ReActAgent
from src.agent.enhance_agent import EnhancedAgent
from src.config import Config

st.set_page_config(page_title="Medical Agent Comparison", page_icon="💊", layout="wide")
st.title("So sánh hai agent y tế")
st.write("Nhập câu hỏi y tế và so sánh câu trả lời của hai agent cùng lúc.")

def _initialize_agents() -> None:
    try:
        llm = Config.get_llm_provider()
        tools = Config.get_tools()
        st.session_state.react_agent = ReActAgent(
            llm=llm,
            tools=tools,
            max_steps=Config.MAX_AGENT_STEPS,
            history_file=Config.HISTORY_FILE
        )
        st.session_state.enhanced_agent = EnhancedAgent(
            llm=llm,
            tools=tools,
            max_steps=Config.MAX_AGENT_STEPS
        )
    except Exception as exc:
        st.error(f"Không thể khởi tạo agent: {exc}")
        st.stop()

if "react_agent" not in st.session_state or st.session_state.get("react_agent") is None:
    _initialize_agents()

if "enhanced_agent" not in st.session_state or st.session_state.get("enhanced_agent") is None:
    _initialize_agents()

if "messages" not in st.session_state:
    st.session_state.messages = []

with st.form(key="medical_agent_form", clear_on_submit=True):
    user_input = st.text_input("Câu hỏi của bạn", "", placeholder="Hỏi về triệu chứng, thuốc, hoặc tư vấn y tế...")
    submit = st.form_submit_button("Gửi")

if submit and user_input.strip():
    react_answer = st.session_state.react_agent.run(user_input)
    enhanced_answer = st.session_state.enhanced_agent.run(user_input)
    st.session_state.messages.append({
        "user": user_input,
        "react": react_answer,
        "enhanced": enhanced_answer,
    })

if st.button("Xoá lịch sử chat"):
    st.session_state.messages = []
    if "react_agent" in st.session_state:
        del st.session_state["react_agent"]
    if "enhanced_agent" in st.session_state:
        del st.session_state["enhanced_agent"]
    st.experimental_rerun() if hasattr(st, "experimental_rerun") else None

for idx, item in enumerate(st.session_state.messages, start=1):
    st.markdown(f"### {idx}. Câu hỏi: {item['user']}")
    left, right = st.columns(2)
    with left:
        st.subheader("Agent ReAct")
        st.info(item["react"])
    with right:
        st.subheader("Agent Nâng Cao")
        st.info(item["enhanced"])
    st.markdown("---")
