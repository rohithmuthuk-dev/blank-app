# NOVA AI — Autonomous Multi-Agent Assistant

NOVA is an Android-friendly Streamlit web app coordinating Planner, Researcher, Coder, Analyst, and Reviewer roles.

## Included
- Task planning and specialist delegation
- GLM / OpenAI-compatible chat-completions API
- Reviewer pass before presenting results
- SQLite conversation memory
- Mobile-friendly Streamlit interface

## Deploy from GitHub
1. Sign in at https://share.streamlit.io/ with GitHub.
2. Select **New app**, repository **rohithmuthuk-dev/blank-app**, branch **main**.
3. Main file: `streamlit_app.py`.
4. In app settings → Secrets, add:
```toml
AI_API_KEY = "your-provider-api-key"
AI_BASE_URL = "https://open.bigmodel.cn/api/paas/v4"
AI_MODEL = "glm-4.5-flash"
```
5. Deploy, then open the app URL on Android Chrome. Use the browser menu → Add to Home screen.

## Security
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
