# NOVA AI — JARVIS-inspired Multi-Agent Assistant

NOVA is an Android-friendly Streamlit assistant that brings the AI brain and specialist-agent workflow from the JARVIS prototype into one app. It is designed for Tamil and English instructions and can be used from an Android browser.

## Current features
- Planner, Researcher, Coder, Analyst and Reviewer agents working as a team.
- Tamil, colloquial Tamil-English and English task instructions.
- User-triggered voice recording and speech-to-text for Tamil or English (India).
- Persistent custom specialist-agent profiles created with the Agent Builder.
- Recent conversation memory stored in local SQLite.
- Optional live web research using OpenRouter's `openrouter:web_search` tool, with source links.
- OpenRouter-compatible model configuration; existing API key configuration is preserved.

## Use it
1. Open the Streamlit app.
2. Type a task or record your voice, then convert and review the transcript.
3. Optionally select one or more custom agents.
4. Optionally enable live web research (additional charges may apply).
5. Run the agent team and review the final answer and agent activity.

## Create a specialist agent
Open **Build your own AI agent → Open Agent Builder**. Give the agent a name and clear role instructions, then save it. Select that agent under **Choose specialist agents for this task** when running a task. Custom agents are additional specialists; the standard Planner, Researcher, Coder, Analyst and Reviewer remain active.

Examples:
- Electrical Testing Engineer — explain CT/PT/VCB/transformer tests, test methods and relevant IEC standards; never invent measured results.
- Android Helper — explain Android settings and app workflows; do not claim to control the phone from this web app.
- App Developer — design and review application code; state clearly when code has not been executed.
- Personal Assistant — organize tasks and prepare drafts; ask for approval before external actions.

## OpenRouter setup
Add secrets in Streamlit app Settings → Secrets. Never put keys in source code or commit them:
```toml
OPENROUTER_API_KEY = "your-openrouter-key"
AI_BASE_URL = "https://openrouter.ai/api/v1"
AI_MODEL = "openrouter/free"
```

## Voice and privacy
- Speech recognition runs only after the user presses **Convert voice to text**.
- The recording is sent to Google's speech-recognition service through SpeechRecognition.
- An internet connection is required; recognition may be unavailable or rate-limited.
- Do not record passwords or sensitive information. Review the transcript before running the task.

## Live web research
- Select **Enable live web research** before running a research task.
- The Researcher can use OpenRouter's web-search server tool and return source links.
- Search usage may incur separate charges in addition to model usage. OpenRouter's published Exa default pricing has been $0.007 per search request; check current pricing before use.
- Search is off by default. No separate search-provider API key is required when the configured OpenRouter account/model supports the tool.

## Safety and limitations
- NOVA can plan tasks, generate code and prepare action instructions. This Streamlit version does not execute arbitrary shell commands, install APKs, control Android apps, tap the screen, send messages, make calls, or change device settings.
- The JARVIS prototype's floating overlay, animated 3D robot, native Android speech/TTS, app launching and Accessibility-based screen interaction belong in a separate native Android companion app. A web page cannot obtain those Android-wide privileges.
- Never automate OTPs, banking, payments, account changes or other sensitive actions without explicit user confirmation and supported native integrations.
- Retrieved webpages are untrusted input; agents are instructed not to follow instructions embedded in them.
- AI-generated code and advice must be reviewed. NOVA does not claim tests were run unless they actually were.
- Conversation memory and custom agent profiles use SQLite on the app's local filesystem. Hosting-platform restarts or storage policies may affect persistence.

## Next milestones
1. Add safe, isolated code execution and real test reporting.
2. Add speech output and a chat-style conversation interface.
3. Build the native Android companion: floating assistant, 3D character, native Tamil/English voice, foreground-service controls, and user-enabled Accessibility actions.
4. Add approval-gated integrations for selected phone tasks.
