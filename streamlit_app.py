import streamlit as st
from src.agent.agent import ReActAgent
from src.config import Config

st.set_page_config(page_title="Medical Agent Chat", page_icon="💊", layout="centered")
st.title("Medical Agent Chat")
st.write("Ask health-related questions and get answers from the medical agent.")

if "agent" not in st.session_state:
    try:
        llm = Config.get_llm_provider()
        tools = Config.get_tools()
        st.session_state.agent = ReActAgent(
            llm=llm,
            tools=tools,
            max_steps=Config.MAX_AGENT_STEPS,
            history_file=Config.HISTORY_FILE
        )
        st.session_state.messages = []
    except Exception as exc:
        st.error(f"Unable to initialize agent: {exc}")
        st.stop()

if "messages" not in st.session_state:
    st.session_state.messages = []

with st.form(key="medical_agent_form", clear_on_submit=True):
    user_input = st.text_input("Your question", "", placeholder="Ask about symptoms, medicines, or general medical advice...")
    submit = st.form_submit_button("Send")

if submit and user_input.strip():
    st.session_state.messages.append({"role": "user", "content": user_input})
    agent: ReActAgent = st.session_state.agent
    answer = agent.run(user_input)
    st.session_state.messages.append({"role": "assistant", "content": answer})

if st.button("Clear chat history"):
    st.session_state.agent.clear_history()
    st.session_state.messages = []
    st.success("Chat history cleared.")

for message in st.session_state.messages:
    role = message["role"]
    content = message["content"]
    if role == "user":
        st.markdown(f"**You:** {content}")
    else:
        st.markdown(f"**Agent:** {content}")
