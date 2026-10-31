# NOVA AI — Autonomous Multi-Agent Assistant

NOVA is an Android-friendly Streamlit web app coordinating Planner, Researcher, Coder, Analyst, and Reviewer roles.

## Included
- Task planning and specialist delegation
- OpenRouter API using the OpenAI-compatible chat-completions endpoint
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

Get an API key at https://openrouter.ai/keys. Check the selected model's pricing and free-tier limits in OpenRouter before use. Never share your key or commit it to GitHub.

## Security and current limitations
- Never commit API keys or credentials.
- This starter does not run arbitrary shell commands or access accounts.
- The Researcher currently prepares research briefs; live web search is a planned integration.
- The Coder drafts code but does not execute it automatically.
- Require approval before external, destructive, or paid actions.

## Next milestones
1. Add live web search for Researcher.
2. Add isolated code execution and real test reporting.
3. Add approval-gated integrations and task automation.
4. Add voice input/output and installable PWA support.
