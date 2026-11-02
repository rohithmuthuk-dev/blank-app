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
    c.execute("""CREATE TABLE IF NOT EXISTS custom_agents(
        id INTEGER PRIMARY KEY, name TEXT NOT NULL UNIQUE,
        instructions TEXT NOT NULL, created_at TEXT NOT NULL)""")
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
    return "\n\n".join(f"Earlier task: {q}\nEarlier answer: {a[:900]}" for q, a in reversed(rows))

def get_custom_agents():
    with db() as c:
        return c.execute("SELECT id,name,instructions FROM custom_agents ORDER BY name").fetchall()

def secret(key, default=""):
    try:
        return str(st.secrets.get(key, default))
    except Exception:
        return default

st.markdown(
    '<div class="nova-hero"><h1>🤖 NOVA AI</h1><b>Autonomous Multi-Agent Assistant</b><p>JARVIS-inspired assistant · Tamil + English · Specialist agents</p></div>',
    unsafe_allow_html=True,
)
with st.sidebar:
    st.subheader("AI provider")
    st.caption("Provider: OpenRouter. Add your key in Streamlit app Settings → Secrets. Never commit API keys.")
    st.code(
        'OPENROUTER_API_KEY = "your-openrouter-key"\nAI_BASE_URL = "https://openrouter.ai/api/v1"\nAI_MODEL = "openrouter/free"',
        language="toml",
    )
    st.caption("Live web search uses OpenRouter and may incur extra charges. NOVA limits each task to at most 2 search calls.")
    if st.button("Clear saved memory"):
        with db() as c:
            c.execute("DELETE FROM conversations")
        st.success("Conversation memory cleared.")
        st.rerun()

st.subheader("🧩 Build your own AI agent")
st.caption("Create a specialist such as Electrical Engineer, Android Helper, App Developer or Personal Assistant.")
with st.expander("Open Agent Builder", expanded=False):
    with st.form("agent_builder", clear_on_submit=True):
        agent_name = st.text_input("Agent name", placeholder="Electrical Testing Engineer")
        agent_instructions = st.text_area(
            "What should this agent do?",
            placeholder="You are an electrical testing specialist. Explain CT, PT, VCB and transformer testing step by step. Use IEC standards where relevant. Never invent test results.",
            height=120,
        )
        create_agent = st.form_submit_button("Save my agent", type="primary")
    if create_agent:
        clean_name = agent_name.strip()
        clean_instructions = agent_instructions.strip()
        if not clean_name or not clean_instructions:
            st.warning("Enter both an agent name and its instructions.")
        elif len(clean_name) > 40 or len(clean_instructions) > 4000:
            st.warning("Keep the name under 40 characters and instructions under 4,000 characters.")
        else:
            try:
                with db() as c:
                    c.execute(
                        "INSERT INTO custom_agents(name,instructions,created_at) VALUES(?,?,?)",
                        (clean_name, clean_instructions, datetime.now(timezone.utc).isoformat()),
                    )
                st.success(f"{clean_name} saved.")
                st.rerun()
            except sqlite3.IntegrityError:
                st.warning("An agent with that name already exists. Choose a different name.")
    existing_agents = get_custom_agents()
    if existing_agents:
        st.markdown("**Your saved agents**")
        for agent_id, name, instructions in existing_agents:
            st.markdown(f"- **{name}** — {instructions[:110]}{'…' if len(instructions) > 110 else ''}")
    else:
        st.info("No custom agents yet. Create your first specialist above.")

st.subheader("Give NOVA a task")
st.caption("Type in Tamil or English, or record your Tamil voice. NOVA will reply in the language you use.")
recording = st.audio_input("🎙️ Record your instruction", sample_rate=16000)
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
        st.success("Voice converted. Check the words below before running NOVA.")
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
saved_agents = get_custom_agents()
agent_lookup = {row[1]: {"name": row[1], "instructions": row[2]} for row in saved_agents}
selected_agent_names = st.multiselect(
    "🧠 Choose specialist agents for this task",
    options=list(agent_lookup.keys()),
    help="Your selected agents work alongside Planner, Researcher, Coder, Analyst and Reviewer.",
)
enable_web_search = st.checkbox(
    "🌐 Enable live web research (up to 2 searches; charges may apply)",
    value=False,
    help="When selected, the Researcher can make at most 2 web-search calls for this task and return source links. Search may incur extra OpenRouter charges. Leave off for ordinary tasks.",
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
        chosen_agents = [agent_lookup[name] for name in selected_agent_names]
        result = NovaOrchestrator(client, progress).run(
            task.strip(), memory(), enable_web_search=enable_web_search,
            custom_agents=chosen_agents,
        )
        if enable_web_search:
            result["web_search_usage"] = {
                "reported": client.web_search_usage_reported,
                "requests": client.web_search_requests_total,
            }
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
    search_usage = result.get("web_search_usage")
    if search_usage:
        if search_usage["reported"]:
            st.caption(
                f"Live web-search requests used: {search_usage['requests']} (maximum 2 for this task)."
            )
        else:
            st.caption(
                "OpenRouter did not return a web-search usage count. Check your OpenRouter activity for billing details."
            )
    with st.expander("See agent activity"):
        for key, value in result.items():
            if key not in ("final", "web_search_usage"):
                label = key.replace("custom_", "").replace("_", " ").title()
                st.markdown(f"**{label} Agent**")
                st.markdown(value)
st.divider()
st.caption("NOVA AI early build · JARVIS Android-wide control and floating 3D character require a native Android companion app. External, sensitive, paid or destructive actions must be approved.")
