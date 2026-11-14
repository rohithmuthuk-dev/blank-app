import unittest

from research_report import build_research_evidence_report


class ResearchEvidenceReportTests(unittest.TestCase):
    def setUp(self):
        self.result = {
            "research_provider": "openrouter",
            "web_search_usage": {
                "reported": True,
                "requests": 1,
                "label": "search requests",
            },
            "web_search_domain_filter": ["iec.ch", "ieee.org"],
            "research_sources": [
                {"title": "IEC official page", "url": "https://iec.ch/standards"},
            ],
            "research_results": [],
            "research": "Researcher brief.",
            "final": "Reviewed answer.",
        }

    def test_report_includes_provider_usage_and_cited_sources(self):
        report = build_research_evidence_report(
            "Research IEC sources", self.result, generated_at="2026-11-11T12:00:00+00:00"
        )
        self.assertIn("Provider: openrouter", report)
        self.assertIn("Provider-reported activity: 1 search requests.", report)
        self.assertIn("[IEC official page](<https://iec.ch/standards>)", report)
        self.assertIn("Enforced domain allowlist: iec\\.ch, ieee\\.org", report)
        self.assertIn("Reviewed answer.", report)

    def test_report_includes_verification_status_and_engineering_checklist(self):
        result = dict(self.result)
        result["research_verification_note"] = (
            "WEB-RESEARCH STATUS: SEARCH ACTIVITY CONFIRMED WITH 1 USABLE CITATION."
        )
        report = build_research_evidence_report("Research", result)
        self.assertIn("Research verification status", report)
        self.assertIn("SEARCH ACTIVITY CONFIRMED", report)
        self.assertIn("Confirm the exact standard number", report)
        self.assertIn("Do not derive relay settings", report)

    def test_report_records_comparative_mode_without_expanding_search_budget(self):
        result = dict(self.result)
        result["research_mode"] = "comparative"
        report = build_research_evidence_report("Compare IEC sources", result)
        self.assertIn("Research approach: Comparative source review", report)
        self.assertIn("existing provider-enforced search/fetch limits are unchanged", report)
        self.assertIn("does not request extra tool calls", report)

    def test_report_distinguishes_retrieved_hits_from_citations(self):
        result = dict(self.result)
        result["research_results"] = [
            {
                "title": "Cited hit",
                "url": "https://iec.ch/standards",
                "snippet": "Official IEC excerpt.",
                "cited": True,
            },
            {
                "title": "Uncited hit",
                "url": "https://ieee.org/standards",
                "snippet": "Retrieved but not cited.",
                "cited": False,
            },
        ]
        report = build_research_evidence_report("Research", result)
        self.assertIn("cited in the answer", report)
        self.assertIn("retrieved, not cited", report)
        self.assertIn("Official IEC excerpt.", report)

    def test_report_explains_when_provider_does_not_expose_raw_hits(self):
        report = build_research_evidence_report("Research", self.result)
        self.assertIn("Raw search-result records were not exposed", report)
        self.assertIn("This does not mean that no results were retrieved", report)

    def test_report_warns_when_usage_metadata_is_missing(self):
        result = dict(self.result)
        result["web_search_usage"] = {"reported": False, "requests": 0}
        report = build_research_evidence_report("Research", result)
        self.assertIn("Do not assume live search occurred", report)

    def test_report_warns_when_provider_reports_zero_search_calls(self):
        result = dict(self.result)
        result["web_search_usage"] = {
            "reported": True, "requests": 0, "label": "web-search tool calls"
        }
        report = build_research_evidence_report("Research", result)
        self.assertIn("reported no search-tool invocation", report)

    def test_private_or_unsafe_source_urls_are_excluded(self):
        result = dict(self.result)
        result["research_sources"] = [
            {"title": "Private", "url": "http://192.168.1.5/admin"},
            {"title": "Script", "url": "javascript:alert(1)"},
        ]
        report = build_research_evidence_report("Research", result)
        self.assertNotIn("192.168.1.5", report)
        self.assertNotIn("javascript:", report)
        self.assertIn("No usable citation URLs were returned", report)

    def test_snippet_backticks_cannot_break_report_code_fence(self):
        result = dict(self.result)
        result["research_results"] = [{
            "title": "Result",
            "url": "https://iec.ch/standards",
            "snippet": "Example with ``` embedded fence",
            "cited": False,
        }]
        report = build_research_evidence_report("Research", result)
        self.assertIn("````", report)

    def test_report_does_not_copy_unrelated_secrets_or_client_state(self):
        result = dict(self.result)
        result["api_key"] = "must-not-appear"
        result["internal_headers"] = {"Authorization": "Bearer must-not-appear"}
        report = build_research_evidence_report("Research", result)
        self.assertNotIn("must-not-appear", report)
        self.assertNotIn("Authorization", report)


if __name__ == "__main__":
    unittest.main()
