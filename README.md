# NOVA AI — Autonomous Multi-Agent Assistant

NOVA is an Android-friendly Streamlit web app coordinating Planner, Researcher, Coder, Analyst, and Reviewer roles.

## Included
- Task planning and specialist delegation
- OpenRouter API using the OpenAI-compatible chat-completions endpoint
- Tamil and English typed instructions
- Tamil voice recording and speech-to-text input (user-triggered)
- Optional live web research using OpenRouter's `openrouter:web_search` server tool
- Source links surfaced from OpenRouter citation annotations when returned
- Reviewer pass before presenting results
- SQLite conversation memory
- Mobile-friendly Streamlit interface

## Deploy from GitHub
1. Sign in at https://share.streamlit.io/ with GitHub.
2. Select **New app**, repository **rohithmuthuk-dev/blank-app**, branch **main**.
3. Main file: `streamlit_app.py`.
4. In app settings → Secrets, add your OpenRouter key:
```toml
OPENROUTER_API_KEY = "your-openrouter-api-key"
AI_BASE_URL = "https://openrouter.ai/api/v1"
AI_MODEL = "openrouter/free"
```
5. Save Secrets. Streamlit should restart the app; if not, reboot it from the app menu.
6. Open the app URL on Android Chrome. Use the browser menu → Add to Home screen.

Get an API key at https://openrouter.ai/keys. Check model pricing and account limits before use. Never share your key or commit it to GitHub.

## Tamil voice input
- Tap the microphone recorder, speak Tamil, then tap **Convert voice to text**.
- Check or edit the transcript before tapping **Run agent team**.
- Tamil is the default speech-recognition language; English (India) can be selected too. Tamil-English mixed speech is supported best when Tamil is the main language.
- Speech-to-text uses the Google speech-recognition service through the SpeechRecognition library. Audio is sent to Google only after the user presses the conversion button. Do not record passwords or sensitive information. Recognition requires an internet connection and may be unavailable or rate-limited.
- NOVA's agents are instructed to understand colloquial Tamil and mixed Tamil-English and reply in the language used by the user.

## Live web research
- In NOVA's task screen, select **Enable live web research** before running a research task.
- The Researcher sends the `openrouter:web_search` server tool with a maximum of 5 results per search and 10 total results per request.
- The model decides when to search and can use results to prepare a cited answer.
- OpenRouter web search has separate usage charges in addition to model usage. Its published Exa default pricing is currently $0.007 per search request; other engines/providers can have different pricing. Check current OpenRouter pricing before enabling it.
- Live search is off by default. No additional search-provider key is required when using the configured OpenRouter API key and a model/account that supports the tool.

## Security and current limitations
- Never commit API keys or credentials.
- Retrieved webpages are untrusted input; NOVA is instructed not to follow instructions embedded in pages.
- This starter does not run arbitrary shell commands or access accounts.
- The Coder drafts code but does not execute it automatically.
- Require approval before external, destructive, or paid actions.

## Next milestones
1. Add isolated code execution and real test reporting.
2. Add approval-gated integrations and task automation.
3. Add voice output and installable PWA support.
