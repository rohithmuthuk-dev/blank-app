# NOVA Electrical AI

**AI-Powered Electrical Testing & Commissioning Assistant** for substation engineers.

NOVA helps engineers prepare test procedures, FAT/SAT plans, commissioning checklists, troubleshooting briefs and draft test reports for CTs, VTs, VCBs, SF6 circuit breakers, transformers, protection relays, cables, busbars and AIS/GIS substations.

## Hackathon build

- Meta Model API (Muse Spark 1.3) integration using the official OpenAI-compatible Responses API.
- OpenRouter remains available as a fallback provider.
- Tamil, colloquial Tamil-English and English instructions.
- Electrical workbench for equipment, deliverable, work stage, voltage class, manufacturer/model and project details.
- Multi-agent Planner, Researcher, Coder, Analyst and Reviewer workflow.
- Optional live web search with source citations (Meta Responses API search grounding or OpenRouter web search).
- User-triggered Tamil/English voice transcription.
- Custom specialist-agent builder and local SQLite conversation memory.
- Responsive Streamlit interface usable from an Android browser.

## Run

```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
```

## Configure API credentials

In Streamlit app Settings → Secrets, add the Meta key received from the Meta Model API dashboard:

```toml
MODEL_API_KEY = "your-meta-model-api-key"
# Optional provider overrides
META_BASE_URL = "https://api.meta.ai/v1"
META_MODEL = "muse-spark-1.3"
```

NOVA prefers Meta Model API whenever `MODEL_API_KEY` is configured. To use OpenRouter instead, omit `MODEL_API_KEY` and configure:

```toml
OPENROUTER_API_KEY = "your-openrouter-key"
AI_BASE_URL = "https://openrouter.ai/api/v1"
AI_MODEL = "openrouter/free"
```

Never commit API keys. The hackathon credit announcement says each participant must claim their own credits; check the Meta dashboard Billing page and ensure the credits are applied before making API calls. The announcement also says a payment card must be on the account to make calls. Set a spend notification if desired.

## Safety and standards integrity

NOVA is engineering decision support, not switching authority or a substitute for an approved method statement. It must not invent IEC clauses, editions, numerical acceptance limits, relay settings, readings or pass/fail results. It distinguishes standard requirements, manufacturer instructions, project/utility specifications and common practice. Where the governing document is unavailable, acceptance criteria are marked **TBC — verify against approved project/manufacturer documents**.

Always follow the approved permit-to-work, isolation, LOTO, prove-dead, discharge, temporary earthing and site safety procedures. Never open an energized CT secondary or short an energized VT secondary. Final procedures, settings and energization decisions require review by the authorized engineer.

Generated test reports are drafts only. Users must enter actual measurements and verify them against approved documents. Voice transcription is sent to Google's speech-recognition service only after the user presses the transcription button; do not record sensitive information.

## Validation

```bash
python -m unittest discover -s tests -v
```

GitHub Actions runs the offline regression suite on pushes and pull requests.

## Current scope and next milestone

This is a mobile-friendly web application, not yet a native Android APK. Native Android floating assistant, 3D avatar, background voice activation and device-wide actions are separate future work and are not claimed as implemented.
