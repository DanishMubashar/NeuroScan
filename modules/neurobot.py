"""
NeuroScan AI - NeuroBot
AI Medical Assistant using Google Gemini via LangChain
"""

import os
import streamlit as st
from dotenv import load_dotenv
from database.db_operations import save_chat_message, get_chat_history, clear_chat_history

load_dotenv()

SYSTEM_PROMPT = """You are NeuroBot, an AI medical assistant inside NeuroScan AI —
a Brain Tumor Detection & Clinical Support System.

Your responsibilities:
1. Answer questions about brain tumors: glioma, meningioma, pituitary, no-tumor
2. Explain MRI scan results, confidence scores, and Grad-CAM heatmaps
3. Help doctors navigate and use the NeuroScan AI system
4. Provide educational information about symptoms, treatment options, and prognosis
5. Explain medical terms in simple language

Rules:
- Be professional, accurate, and empathetic
- Always clarify you are an AI and cannot replace a real doctor
- Never prescribe medications or make final diagnoses
- Keep answers concise but complete
"""


def _get_gemini_response(messages: list) -> str:
    try:
        from langchain_google_genai import ChatGoogleGenerativeAI
        from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            return (
                "⚠️ Google API key not set.\n\n"
                "Please add `GOOGLE_API_KEY=your_key` to your `.env` file.\n"
                "Get a free key at: https://aistudio.google.com/app/apikey"
            )

        llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=api_key,
            temperature=0.7
        )

        lc_msgs = [SystemMessage(content=SYSTEM_PROMPT)]
        for m in messages:
            if m["role"] == "user":
                lc_msgs.append(HumanMessage(content=m["content"]))
            else:
                lc_msgs.append(AIMessage(content=m["content"]))

        return llm.invoke(lc_msgs).content

    except ImportError:
        return "⚠️ Install langchain-google-genai: `pip install langchain-google-genai`"
    except Exception as e:
        return f"⚠️ NeuroBot error: {e}"


def render_neurobot(doctor_id: int):
    st.markdown("## 🤖 NeuroBot — AI Medical Assistant")
    st.caption("Ask anything about brain tumors, MRI analysis, or NeuroScan AI. "
               "NeuroBot cannot replace professional medical advice.")

    # Init session messages from DB
    if "neurobot_messages" not in st.session_state:
        history = get_chat_history(doctor_id, limit=50)
        st.session_state["neurobot_messages"] = [
            {"role": r["role"], "content": r["message"]} for r in history
        ]

    # Clear button
    _, col_btn = st.columns([5, 1])
    with col_btn:
        if st.button("🗑️ Clear", help="Clear chat history"):
            clear_chat_history(doctor_id)
            st.session_state["neurobot_messages"] = []
            st.rerun()

    # Display messages
    if not st.session_state["neurobot_messages"]:
        st.markdown("""
        <div style='text-align:center;color:#666;padding:3rem 0;'>
            <div style='font-size:3rem;'>🤖</div>
            <div style='font-size:1.1rem;margin-top:0.5rem;color:#aaa;'>Hi! I'm NeuroBot.</div>
            <div style='font-size:0.85rem;margin-top:0.3rem;'>
                Ask me about brain tumors, scan results, or system usage.
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Suggestion buttons
        st.markdown("**💡 Suggested Questions:**")
        suggestions = [
            "What is a Glioma tumor?",
            "How does Grad-CAM work?",
            "What does confidence score mean?",
            "Symptoms of brain tumors?",
            "Difference between glioma and meningioma?",
            "How to add a new patient?",
        ]
        cols = st.columns(3)
        for i, s in enumerate(suggestions):
            with cols[i % 3]:
                if st.button(s, key=f"sug_{i}", use_container_width=True):
                    st.session_state["_quick_q"] = s
                    st.rerun()
    else:
        for msg in st.session_state["neurobot_messages"]:
            avatar = "🤖" if msg["role"] == "assistant" else "👨‍⚕️"
            with st.chat_message(msg["role"], avatar=avatar):
                st.markdown(msg["content"])

    # Handle suggestion click
    if "_quick_q" in st.session_state:
        _send(st.session_state.pop("_quick_q"), doctor_id)
        st.rerun()

    # Chat input
    if prompt := st.chat_input("Ask NeuroBot..."):
        _send(prompt, doctor_id)
        st.rerun()


def _send(user_input: str, doctor_id: int):
    st.session_state["neurobot_messages"].append(
        {"role": "user", "content": user_input}
    )
    save_chat_message(doctor_id, "user", user_input)

    with st.spinner("NeuroBot is thinking..."):
        reply = _get_gemini_response(st.session_state["neurobot_messages"])

    st.session_state["neurobot_messages"].append(
        {"role": "assistant", "content": reply}
    )
    save_chat_message(doctor_id, "assistant", reply)
