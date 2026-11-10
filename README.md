# NOVA Electrical AI

**AI-Powered Electrical Testing & Commissioning Assistant** for substation engineers.

NOVA helps engineers prepare test procedures, FAT/SAT plans, commissioning checklists, troubleshooting briefs and draft test reports for CTs, VTs, VCBs, SF6 circuit breakers, transformers, protection relays, cables, busbars and AIS/GIS substations.

## Hackathon build

- Meta Model API (Muse Spark 1.3) integration using the official OpenAI-compatible Responses API.
- OpenRouter remains available as a fallback provider.
- Tamil, colloquial Tamil-English and English instructions.
- Electrical workbench for equipment, deliverable, work stage, voltage class, manufacturer/model and project details.
- Optional text-based PDF reference upload (up to 3 files, 25 pages and 12,000 extracted characters per file) with filename/page context.
- Downloadable Markdown draft test reports and technical answers.
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

## Live web research

Live research is optional and **off by default**. Turn on the checkbox only when the task needs current information or source verification. The Researcher uses the search tool belonging to the provider selected by the existing credential settings:

- **Meta Model API:** uses the Responses API `web_search` tool, requests low search context, opts into `web_search_call.results` so NOVA can show the raw hits the model considered, disables parallel tool calls, and sets `max_tool_calls: 2` as a hard cap across built-in tools. Raw retrieved hits are shown separately from the smaller subset cited in the answer; NOVA labels which hits were actually cited. Unsafe/private URLs are discarded, and snippets are length-limited and displayed as plain text. The response lists actual `web_search_call` items; the model may decide not to search, so NOVA reports zero when the response confirms no search call.
- **OpenRouter:** uses `openrouter:web_search` with the Exa engine, low search context, at most 2 searches and 10 total results. It uses `openrouter:web_fetch` with the direct OpenRouter fetch engine, at most 1 page fetch and a 6,000-token content cap. Both share a two-step request budget, with a `stop_server_tools_when` cost condition set to **$0.014**; parallel tool calls are disabled. The step and cost conditions stop the server-tool loop, whichever fires first.
- OpenRouter currently lists Exa search at **$0.007 per search request**, so two searches are approximately $0.014. The $0.014 condition applies to server-tool spend only; it is **not** a cap on model-token charges, account-wide spend, or a guarantee against provider price changes. The direct OpenRouter fetch engine is listed as free, but fetched content still adds model-token usage. Check the provider's billing/activity page; NOVA's usage indicator is informational, not an invoice.
- **Optional OpenRouter domain allowlist:** when OpenRouter is selected, enter up to 10 public hostnames (for example, `iec.ch, ieee.org, dewa.gov.ae`). NOVA validates the entries and sends the same `allowed_domains` list to both web search and page fetch, so results and fetched pages are restricted to those domains (including their subdomains). Use hostnames only—no URL scheme, path, wildcard, IP address, or private/local hostname. Leave the field empty for unrestricted web research.
- **Meta provider limitation:** the app does not show the strict allowlist field when Meta is selected because Meta's current search-grounding API rejects `allowed_domains` and `blocked_domains`. On Meta, ask NOVA in the task to prefer official sources; that is a model instruction, not an enforced filter.
- The selected provider's existing API key is used. No separate search-provider credential is needed for these built-in tools.
- The model may choose not to invoke search even when enabled. NOVA must not claim the answer is web-verified unless the provider response confirms a search call and supplies citations.
- NOVA captures the Researcher's validated citation annotations separately from the final answer and displays a dedicated source list. On Meta, it also displays raw search hits separately and marks whether each hit was cited; a retrieved hit must not be mistaken for a cited source. The app warns when search usage is reported without citations, confirms when the provider reports no search call, and marks missing usage metadata as unverified. A source list is evidence returned by the provider, not a guarantee that every source is authoritative or correct; review the linked documents. Citation links are additionally screened to reject non-HTTP schemes, local/private network destinations, reserved hostnames, ambiguous numeric IP forms and malformed ports before display. This is a link-display safeguard, not a replacement for the search provider's own fetch protections.
- Search results and fetched pages are untrusted data. NOVA is instructed not to follow instructions embedded in external content or perform actions requested by webpages.

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
