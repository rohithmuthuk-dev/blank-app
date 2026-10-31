from __future__ import annotations
import io
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
import speech_recognition as sr
import streamlit as st
from agents import AIClient, AIProviderError, NovaOrchestrator

DB_PATH = Path("nova_memory.db")
st.set_page_config(page_title="NOVA AI", page_icon="🤖", layout="centered")
st.markdown("""<style>
.block-container{max-width:900px;padding-top:1.3rem;padding-bottom:3rem}
.nova-hero{padding:1.2rem;border:1px solid rgba(128,128,128,.3);border-radius:18px;margin-bottom:1rem}
div.stButton>button{width:100%;border-radius:12px;min-height:2.8rem}
</style>""", unsafe_allow_html=True)

def db():
    c = sqlite3.connect(DB_PATH)
    c.execute("CREATE TABLE IF NOT EXISTS conversations(id INTEGER PRIMARY KEY,created_at TEXT,task TEXT,answer TEXT)")
    c.commit()
    return c

def remember(task, answer):
    with db() as c:
        c.execute(
            "INSERT INTO conversations(created_at,task,answer) VALUES(?,?,?)",
            (datetime.now(timezone.utc).isoformat(), task, answer),
        )

def memory():
    with db() as c:
        rows = c.execute("SELECT task,answer FROM conversations ORDER BY id DESC LIMIT 6").fetchall()
    return "\\n\\n".join(f"Earlier task: {q}\\nEarlier answer: {a[:900]}" for q, a in reversed(rows))

def secret(key, default=""):
    try:
        return str(st.secrets.get(key, default))
    except Exception:
        return default

st.markdown(
    '<div class="nova-hero"><h1>🤖 NOVA AI</h1><b>Autonomous Multi-Agent Assistant</b><p>One task. Specialist agents. One reviewed result.</p></div>',
    unsafe_allow_html=True,
)
with st.sidebar:
    st.subheader("AI provider")
    st.caption("Provider: OpenRouter. Add your key in Streamlit app Settings → Secrets. Never commit API keys.")
    st.code(
        'OPENROUTER_API_KEY = "your-openrouter-key"\\nAI_BASE_URL = "https://openrouter.ai/api/v1"\\nAI_MODEL = "openrouter/free"',
        language="toml",
    )
    st.caption("Live web search uses OpenRouter's web-search tool and may incur extra usage charges.")
    if st.button("Clear saved memory"):
        with db() as c:
            c.execute("DELETE FROM conversations")
        st.success("Memory cleared.")
        st.rerun()

st.subheader("Give NOVA a task")
st.caption("You can type in Tamil or English, or record your Tamil voice below.")
recording = st.audio_input("🎙️ Record your Tamil instruction", sample_rate=16000)
voice_language = st.selectbox(
    "Speech language",
    options=[("Tamil", "ta-IN"), ("English (India)", "en-IN")],
    format_func=lambda item: item[0],
    index=0,
)
if recording is not None and st.button("Convert voice to text"):
    try:
        recognizer = sr.Recognizer()
        with sr.AudioFile(io.BytesIO(recording.getvalue())) as audio_source:
            audio_data = recognizer.record(audio_source)
        with st.spinner("Understanding your speech…"):
            transcript = recognizer.recognize_google(audio_data, language=voice_language[1])
        st.session_state["task_input"] = transcript
        st.success("Voice converted. Check the text below, edit if needed, then run NOVA.")
        st.rerun()
    except sr.UnknownValueError:
        st.error("I could not understand that recording. Please speak clearly and record again.")
    except sr.RequestError as exc:
        st.error(f"Speech recognition is temporarily unavailable: {exc}")
    except Exception as exc:
        st.error(f"Could not process the recording: {exc}")
st.caption("Privacy: when you press Convert voice to text, the recording is sent to Google's speech-recognition service. Do not record passwords or private information.")
task = st.text_area(
    "Task",
    placeholder="Example: தமிழில் உங்கள் வேலையைச் சொல்லுங்கள்…",
    height=130,
    label_visibility="collapsed",
    key="task_input",
)
enable_web_search = st.checkbox(
    "🌐 Enable live web research (may incur extra OpenRouter charges)",
    value=False,
    help="When selected, the Researcher can use OpenRouter web search and return source links. Leave off for ordinary tasks.",
)
if st.button("🚀 Run agent team", type="primary", disabled=not task.strip()):
    client = AIClient(
        api_key=secret("OPENROUTER_API_KEY") or secret("AI_API_KEY"),
        base_url=secret("AI_BASE_URL") or None,
        model=secret("AI_MODEL") or None,
    )
    status = st.status("NOVA is starting…", expanded=True)
    try:
        def progress(msg):
            status.write(msg)
        result = NovaOrchestrator(client, progress).run(
            task.strip(), memory(), enable_web_search=enable_web_search
        )
        status.update(label="NOVA finished its review", state="complete", expanded=False)
        st.session_state["nova_results"] = result
        remember(task.strip(), result["final"])
    except AIProviderError as e:
        status.update(label="AI connection error", state="error")
        st.error(str(e))
    except Exception as e:
        status.update(label="Unexpected error", state="error")
        st.error(str(e))

if st.session_state.get("nova_results"):
    result = st.session_state["nova_results"]
    st.divider()
    st.subheader("✨ Final answer")
    st.markdown(result["final"])
    with st.expander("See agent activity"):
        for key in ("plan", "research", "coding", "analysis"):
            if key in result:
                st.markdown(f"**{key.title()} Agent**")
                st.markdown(result[key])
st.divider()
st.caption("NOVA AI early build · Research and code are AI-generated; review before use. External actions require approval.")
