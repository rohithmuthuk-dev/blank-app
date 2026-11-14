"""Build a portable, source-auditable Markdown report from a NOVA research run."""
from __future__ import annotations

import re
from datetime import datetime, timezone

from agents import RESEARCH_MODE_LABELS, normalize_public_http_url


def _clean_text(value, limit=4000):
    text = str(value or "").replace("\r\n", "\n").replace("\r", "\n")
    text = "".join(
        char for char in text
        if char in ("\n", "\t") or (ord(char) >= 32 and ord(char) != 127)
    )
    return text[:limit].strip()


def _escape_markdown(value):
    text = _clean_text(value)
    return re.sub(r"([\\`*_{}\[\]()#+\-.!|>])", r"\\\1", text)


def _code_fence(value):
    runs = [len(match.group(0)) for match in re.finditer(r"`+", value)]
    return "`" * max(3, (max(runs) + 1) if runs else 3)


def _safe_sources(items, limit):
    safe = []
    seen = set()
    for item in items if isinstance(items, list) else []:
        if not isinstance(item, dict):
            continue
        url = normalize_public_http_url(item.get("url"))
        if not url or url in seen:
            continue
        seen.add(url)
        safe.append({
            "title": _clean_text(item.get("title") or url, 240),
            "url": url,
            "snippet": _clean_text(item.get("snippet"), 1000),
            "cited": bool(item.get("cited")),
        })
        if len(safe) >= limit:
            break
    return safe


def build_research_evidence_report(task, result, generated_at=None):
    """Create a Markdown evidence pack without including credentials or hidden state.

    Retrieved search hits and answer citations remain separate. A provider that
    exposes citations but not raw hits is described accurately rather than
    having search results inferred or fabricated.
    """
    result = result if isinstance(result, dict) else {}
    timestamp = generated_at or datetime.now(timezone.utc).isoformat(timespec="seconds")
    provider = _clean_text(result.get("research_provider") or "Unknown provider", 80)
    usage = result.get("web_search_usage")
    citations = _safe_sources(result.get("research_sources"), 30)
    hits = _safe_sources(result.get("research_results"), 10)
    domains = result.get("web_search_domain_filter") or []

    lines = [
        "# NOVA AI — Research Evidence Report",
        "",
        f"- Generated (UTC): {_escape_markdown(timestamp)}",
        f"- Provider: {_escape_markdown(provider)}",
        f"- Task: {_escape_markdown(task)}",
    ]
    research_mode = result.get("research_mode")
    mode_label = (
        RESEARCH_MODE_LABELS.get(research_mode, "Focused lookup")
        if isinstance(research_mode, str) else "Focused lookup"
    )
    lines.append(f"- Research approach: {_escape_markdown(mode_label)}")
    if research_mode == "comparative":
        lines.append(
            "- Search limits: existing provider-enforced search/fetch limits are unchanged; "
            "comparative mode does not request extra tool calls."
        )
    if isinstance(domains, (list, tuple)) and domains:
        lines.append("- Enforced domain allowlist: " + ", ".join(
            _escape_markdown(domain) for domain in domains[:10]
        ))
    else:
        lines.append("- Enforced domain allowlist: none")

    lines.extend(["", "## Search activity"])
    if isinstance(usage, dict) and usage.get("reported") is True:
        try:
            count = int(usage.get("requests", 0))
            if isinstance(usage.get("requests"), bool) or count < 0:
                raise ValueError
        except (TypeError, ValueError):
            lines.append("Provider usage metadata was marked reported but contained an invalid count.")
        else:
            label = _escape_markdown(usage.get("label") or "search requests")
            lines.append(f"Provider-reported activity: {count} {label}.")
            if count == 0:
                lines.append("The provider reported no search-tool invocation; this answer is not web-verified.")
    else:
        lines.append(
            "The provider did not return verifiable search-usage metadata. "
            "Do not assume live search occurred."
        )

    verification_note = _clean_text(result.get("research_verification_note"), 1200)
    lines.extend(["", "## Research verification status"])
    lines.append(
        verification_note
        or "No Researcher-time verification status was captured; do not assume live search occurred."
    )

    lines.extend(["", "## Electrical engineering verification checklist"])
    lines.extend([
        "- [ ] Confirm the exact standard number, edition, amendments and clause in the approved source copy.",
        "- [ ] Separate normative requirements from informative guidance, manufacturer instructions and project or utility specifications.",
        "- [ ] Verify every numerical acceptance limit against the approved project, utility and manufacturer documents.",
        "- [ ] Do not derive relay settings, CT/VT limits, trip logic or pass/fail decisions from search snippets alone.",
    ])

    lines.extend(["", "## Sources cited in the Researcher answer"])
    if citations:
        for source in citations:
            title = _escape_markdown(source["title"] or source["url"])
            lines.append(f"- [{title}](<{source['url']}>)")
    else:
        lines.append("No usable citation URLs were returned. Treat the answer as not independently source-verified.")

    lines.extend(["", "## Search results exposed by the provider"])
    if hits:
        for index, source in enumerate(hits, start=1):
            title = _escape_markdown(source["title"] or source["url"])
            status = "cited in the answer" if source["cited"] else "retrieved, not cited"
            lines.append(f"{index}. [{title}](<{source['url']}>) — {status}")
            if source["snippet"]:
                fence = _code_fence(source["snippet"])
                lines.extend(["", fence, source["snippet"], fence])
    elif citations:
        lines.append(
            "Raw search-result records were not exposed to this app by the selected provider integration. "
            "This does not mean that no results were retrieved."
        )
    else:
        lines.append("No provider-exposed raw search-result records are available.")

    research_brief = _clean_text(result.get("research"), 30000)
    if research_brief:
        lines.extend(["", "## Researcher brief", "", research_brief])

    final_answer = _clean_text(result.get("final"), 50000)
    if final_answer:
        lines.extend(["", "## Reviewed final answer", "", final_answer])

    lines.extend([
        "",
        "---",
        "NOVA output is decision support, not an approved test procedure or switching authority. "
        "Verify standards editions, clauses, acceptance criteria and safety steps against the approved "
        "project documents, manufacturer instructions and site procedures. Search citations are not "
        "a guarantee that a source is authoritative or that every claim is correct.",
        "",
    ])
    return "\n".join(lines)
