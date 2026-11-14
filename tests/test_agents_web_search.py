import unittest
from unittest.mock import patch

from agents import (
    AIClient, AIProviderError, NovaOrchestrator, build_research_verification_note,
    normalize_allowed_domains, normalize_public_http_url, normalize_research_mode,
)


class FakeResponse:
    def __init__(self, message, usage=None):
        self.message = message
        self.usage = usage

    def raise_for_status(self):
        return None

    def json(self):
        data = {"choices": [{"message": self.message}]}
        if self.usage is not None:
            data["usage"] = self.usage
        return data


class FakeMetaResponse:
    def __init__(self, data):
        self.data = data

    def raise_for_status(self):
        return None

    def json(self):
        return self.data


class AIClientWebSearchTests(unittest.TestCase):
    def setUp(self):
        self.client = AIClient(api_key="test-key", model="test-model")

    @patch("agents.requests.post")
    def test_web_search_is_disabled_by_default(self, post):
        post.return_value = FakeResponse({"content": "Hello"})
        self.client.chat("system", "hello")
        payload = post.call_args.kwargs["json"]
        self.assertNotIn("tools", payload)
        self.assertNotIn("max_tool_calls", payload)
        self.assertNotIn("stop_server_tools_when", payload)
        self.assertNotIn("parallel_tool_calls", payload)

    @patch("agents.requests.post")
    def test_web_search_has_a_two_call_limit(self, post):
        post.return_value = FakeResponse({"content": "Research result"})
        self.client.chat("system", "research this", enable_web_search=True)
        payload = post.call_args.kwargs["json"]
        self.assertNotIn("max_tool_calls", payload)
        self.assertFalse(payload["parallel_tool_calls"])
        self.assertEqual(payload["stop_server_tools_when"], [
            {"type": "step_count_is", "step_count": 2},
            {"type": "max_cost", "max_cost_in_dollars": 0.014},
        ])
        self.assertEqual(payload["tools"][0]["parameters"]["engine"], "exa")
        self.assertEqual(payload["tools"][0]["parameters"]["search_context_size"], "low")
        self.assertEqual(payload["tools"][0]["parameters"]["max_uses"], 2)
        self.assertEqual(payload["tools"][0]["parameters"]["max_total_results"], 10)
        self.assertEqual(payload["tools"][1]["type"], "openrouter:web_fetch")
        self.assertEqual(payload["tools"][1]["parameters"]["engine"], "openrouter")
        self.assertEqual(payload["tools"][1]["parameters"]["max_uses"], 1)
        self.assertEqual(payload["tools"][1]["parameters"]["max_content_tokens"], 6000)

    @patch("agents.requests.post")
    def test_domain_allowlist_reaches_both_openrouter_tools(self, post):
        post.return_value = FakeResponse({"content": "Filtered research."})
        self.client.chat(
            "system", "research official sources",
            enable_web_search=True,
            allowed_domains=["IEC.CH", "dewa.gov.ae"],
        )
        payload = post.call_args.kwargs["json"]
        expected = ["iec.ch", "dewa.gov.ae"]
        self.assertEqual(payload["tools"][0]["parameters"]["allowed_domains"], expected)
        self.assertEqual(payload["tools"][1]["parameters"]["allowed_domains"], expected)

    @patch("agents.requests.post")
    def test_meta_rejects_unsupported_domain_filter_before_network(self, post):
        client = AIClient(api_key="meta-test", provider="meta")
        with self.assertRaisesRegex(AIProviderError, "not supported by the Meta web-search API"):
            client.chat(
                "system", "research",
                enable_web_search=True,
                allowed_domains=["iec.ch"],
            )
        post.assert_not_called()

    @patch("agents.requests.post")
    def test_url_citations_are_added_to_the_answer(self, post):
        post.return_value = FakeResponse({
            "content": "A sourced answer.",
            "annotations": [{
                "type": "url_citation",
                "url_citation": {
                    "url": "https://example.com/article",
                    "title": "Example article",
                },
            }],
        })
        answer = self.client.chat("system", "research")
        self.assertIn("[Example article](<https://example.com/article>)", answer)
        self.assertEqual(self.client.last_citations, [{
            "title": "Example article",
            "url": "https://example.com/article",
        }])


    @patch("agents.requests.post")
    def test_non_http_citations_are_ignored(self, post):
        post.return_value = FakeResponse({
            "content": "A sourced answer.",
            "annotations": [
                {"url_citation": {"url": "javascript:alert(1)", "title": "Unsafe"}},
                {"url_citation": {"url": "data:text/html,hello", "title": "Data URL"}},
                {"url_citation": {"url": "http://127.0.0.1/admin", "title": "Loopback"}},
                {"url_citation": {"url": "http://169.254.169.254/latest/meta-data", "title": "Cloud metadata"}},
                {"url_citation": {"url": "http://127.1/private", "title": "Short IPv4"}},
                {"url_citation": {"url": "https://router.local/status", "title": "Local network"}},
                {"url_citation": {"url": "https://safe.example.com/article", "title": "Safe"}},
            ],
        })
        answer = self.client.chat("system", "research")
        self.assertIn("https://safe.example.com/article", answer)
        self.assertNotIn("javascript:", answer)
        self.assertNotIn("data:text/html", answer)
        self.assertEqual(
            [source["url"] for source in self.client.last_citations],
            ["https://safe.example.com/article"],
        )

    @patch("agents.requests.post")
    def test_citation_title_cannot_break_markdown_link(self, post):
        post.return_value = FakeResponse({
            "content": "A sourced answer.",
            "annotations": [{
                "url_citation": {
                    "url": "https://example.com/article",
                    "title": "Bad ](https://attacker.example)",
                },
            }],
        })
        answer = self.client.chat("system", "research")
        self.assertIn(r"Bad \]", answer)
        self.assertIn("](<https://example.com/article>)", answer)

    @patch("agents.requests.post")
    def test_server_tool_usage_is_recorded(self, post):
        post.return_value = FakeResponse(
            {"content": "Searched answer"},
            usage={"server_tool_use_details": {"web_search_requests": 2}},
        )
        self.client.chat("system", "research", enable_web_search=True)
        self.assertTrue(self.client.web_search_usage_reported)
        self.assertEqual(self.client.web_search_requests_total, 2)

    @patch("agents.requests.post")
    def test_legacy_server_tool_usage_field_is_supported(self, post):
        post.return_value = FakeResponse(
            {"content": "Searched answer"},
            usage={"server_tool_use": {"web_search_requests": 1}},
        )
        self.client.chat("system", "research", enable_web_search=True)
        self.assertTrue(self.client.web_search_usage_reported)
        self.assertEqual(self.client.web_search_requests_total, 1)

    @patch("agents.requests.post")
    def test_invalid_server_tool_usage_is_not_reported_as_zero(self, post):
        post.return_value = FakeResponse(
            {"content": "Searched answer"},
            usage={"server_tool_use_details": {"web_search_requests": "unknown"}},
        )
        self.client.chat("system", "research", enable_web_search=True)
        self.assertFalse(self.client.web_search_usage_reported)

    @patch("agents.requests.post")
    def test_missing_server_tool_usage_is_not_reported_as_zero(self, post):
        post.return_value = FakeResponse({"content": "Answer"})
        self.client.chat("system", "research", enable_web_search=True)
        self.assertFalse(self.client.web_search_usage_reported)

    @patch("agents.requests.post")
    def test_usage_metadata_resets_between_research_requests(self, post):
        post.side_effect = [
            FakeResponse(
                {"content": "First answer"},
                usage={"server_tool_use_details": {"web_search_requests": 2}},
            ),
            FakeResponse({"content": "Second answer"}),
        ]
        self.client.chat("system", "first", enable_web_search=True)
        self.assertTrue(self.client.web_search_usage_reported)
        self.assertEqual(self.client.web_search_requests_total, 2)

        self.client.chat("system", "second", enable_web_search=True)
        self.assertFalse(self.client.web_search_usage_reported)
        self.assertEqual(self.client.web_search_requests_total, 0)

    def test_research_verification_note_distinguishes_provider_states(self):
        citation = [{"title": "IEC", "url": "https://iec.ch"}]
        self.assertIn(
            "UNCONFIRMED",
            build_research_verification_note({"reported": False, "requests": 0}, citation),
        )
        self.assertIn(
            "NO LIVE SEARCH",
            build_research_verification_note({"reported": True, "requests": 0}, []),
        )
        self.assertIn(
            "INCONSISTENT",
            build_research_verification_note({"reported": True, "requests": 0}, citation),
        )
        self.assertIn(
            "NO USABLE CITATIONS",
            build_research_verification_note({"reported": True, "requests": 1}, []),
        )
        self.assertIn(
            "SEARCH ACTIVITY CONFIRMED",
            build_research_verification_note({"reported": True, "requests": 1}, citation),
        )

    def test_missing_key_fails_before_network_request(self):
        client = AIClient(api_key="")
        with self.assertRaises(AIProviderError):
            client.chat("system", "hello")


class ResearchModeValidationTests(unittest.TestCase):
    def test_supported_modes_are_normalized(self):
        self.assertEqual(normalize_research_mode(" FOCUSED "), "focused")
        self.assertEqual(normalize_research_mode("Comparative"), "comparative")

    def test_unknown_mode_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "focused or comparative"):
            normalize_research_mode("unlimited")


class ResearchDomainValidationTests(unittest.TestCase):
    def test_normalizes_and_deduplicates_public_domains(self):
        self.assertEqual(
            normalize_allowed_domains("IEC.CH; dewa.gov.ae\niec.ch"),
            ["iec.ch", "dewa.gov.ae"],
        )

    def test_empty_domain_filter_is_allowed(self):
        self.assertEqual(normalize_allowed_domains("  , ;  "), [])

    def test_rejects_urls_paths_ip_and_private_hostnames(self):
        invalid = [
            "https://iec.ch",
            "example.com/private/path",
            "127.0.0.1",
            "localhost",
            "intranet.local",
            "*.example.com",
            "source.example",
            "router.home.arpa",
            "device.lan",
            "server.corp",
            "hidden.onion",
            "0177.0.0.1",
            "0x7f.0.0.1",
            "example.123",
        ]
        for domain in invalid:
            with self.subTest(domain=domain):
                with self.assertRaises(ValueError):
                    normalize_allowed_domains(domain)

    def test_rejects_more_than_ten_domains(self):
        domains = [f"source{i}.example.com" for i in range(11)]
        with self.assertRaisesRegex(ValueError, "no more than 10"):
            normalize_allowed_domains(domains)


class ResearchCitationUrlSafetyTests(unittest.TestCase):
    def test_accepts_public_http_and_https_urls(self):
        self.assertEqual(
            normalize_public_http_url("https://iec.ch/standards?edition=2026"),
            "https://iec.ch/standards?edition=2026",
        )
        self.assertEqual(
            normalize_public_http_url("http://8.8.8.8/status"),
            "http://8.8.8.8/status",
        )

    def test_rejects_private_reserved_and_ambiguous_hosts(self):
        unsafe = [
            "http://localhost/",
            "http://service.local/",
            "http://api.internal/",
            "http://printer.home.arpa/",
            "http://127.0.0.1/",
            "http://127.1/",
            "http://2130706433/",
            "http://0x7f000001/",
            "http://10.0.0.1/",
            "http://172.16.0.1/",
            "http://192.168.1.10/",
            "http://169.254.169.254/latest/meta-data/",
            "http://[::1]/",
            "http://[fe80::1]/",
            "http://example.com:99999/",
            "http://user@example.com/",
            "javascript:alert(1)",
            "file:///etc/passwd",
        ]
        for url in unsafe:
            with self.subTest(url=url):
                self.assertIsNone(normalize_public_http_url(url))

    def test_rejects_malformed_urls_and_control_characters(self):
        for url in (
            "https://",
            "https://example.com\\\\@evil.test",
            "https://example.com/\\nnext",
        ):
            with self.subTest(url=url):
                self.assertIsNone(normalize_public_http_url(url))

    @patch("agents.requests.post")
    def test_meta_citations_reject_private_and_local_destinations(self, post):
        post.return_value = FakeMetaResponse({
            "output_text": "Meta research answer.",
            "output": [{
                "type": "message",
                "content": [{
                    "type": "output_text",
                    "text": "Meta research answer.",
                    "annotations": [
                        {"url_citation": {"url": "http://10.0.0.5/admin", "title": "Private"}},
                        {"url_citation": {"url": "https://iec.ch/standards", "title": "IEC"}},
                    ],
                }],
            }, {"type": "web_search_call"}],
        })
        client = AIClient(api_key="meta-test", provider="meta")
        answer = client.chat("system", "research", enable_web_search=True)
        self.assertIn("IEC", answer)
        self.assertNotIn("10.0.0.5", answer)
        self.assertEqual(client.last_citations, [{
            "title": "IEC",
            "url": "https://iec.ch/standards",
        }])



class MetaSearchResultAuditTests(unittest.TestCase):
    @patch("agents.requests.post")
    def test_meta_requests_raw_results_with_existing_two_call_cap(self, post):
        post.return_value = FakeMetaResponse({
            "output_text": "Grounded answer.",
            "output": [{"type": "web_search_call", "results": []}],
        })
        client = AIClient(api_key="meta-test", provider="meta")
        client.chat("system", "research", enable_web_search=True)
        payload = post.call_args.kwargs["json"]
        self.assertEqual(payload["include"], ["web_search_call.results"])
        self.assertEqual(payload["max_tool_calls"], 2)
        self.assertFalse(payload["parallel_tool_calls"])

    @patch("agents.requests.post")
    def test_meta_keeps_retrieved_hits_separate_from_cited_sources(self, post):
        post.return_value = FakeMetaResponse({
            "output_text": "IEC is cited in this answer.",
            "output": [
                {
                    "type": "web_search_call",
                    "results": [
                        {
                            "type": "text_result",
                            "title": "IEC official page",
                            "url": "https://iec.ch/standards",
                            "snippet": "Official IEC standards information.",
                        },
                        {
                            "type": "text_result",
                            "title": "IEEE result not cited",
                            "url": "https://ieee.org/standards",
                            "snippet": "Retrieved but not cited.",
                        },
                        {
                            "type": "text_result",
                            "title": "Unsafe internal result",
                            "url": "http://192.168.1.10/admin",
                            "snippet": "Must be discarded.",
                        },
                    ],
                },
                {
                    "type": "message",
                    "content": [{
                        "type": "output_text",
                        "text": "IEC is cited in this answer.",
                        "annotations": [{
                            "type": "url_citation",
                            "url": "https://iec.ch/standards",
                            "title": "IEC official page",
                        }],
                    }],
                },
            ],
        })
        client = AIClient(api_key="meta-test", provider="meta")
        client.chat("system", "research", enable_web_search=True)
        self.assertEqual(len(client.last_citations), 1)
        self.assertEqual(
            client.last_search_results,
            [
                {
                    "title": "IEC official page",
                    "url": "https://iec.ch/standards",
                    "snippet": "Official IEC standards information.",
                    "cited": True,
                },
                {
                    "title": "IEEE result not cited",
                    "url": "https://ieee.org/standards",
                    "snippet": "Retrieved but not cited.",
                    "cited": False,
                },
            ],
        )

    @patch("agents.requests.post")
    def test_meta_search_result_text_is_bounded(self, post):
        post.return_value = FakeMetaResponse({
            "output_text": "Answer.",
            "output": [{
                "type": "web_search_call",
                "results": [{
                    "title": "T" * 300,
                    "url": "https://example.com/result",
                    "snippet": "S" * 1500,
                }],
            }],
        })
        client = AIClient(api_key="meta-test", provider="meta")
        client.chat("system", "research", enable_web_search=True)
        self.assertEqual(len(client.last_search_results[0]["title"]), 240)
        self.assertEqual(len(client.last_search_results[0]["snippet"]), 1000)

    @patch("agents.requests.post")
    def test_meta_search_results_are_reset_for_non_search_request(self, post):
        post.side_effect = [
            FakeMetaResponse({
                "output_text": "Searched.",
                "output": [{
                    "type": "web_search_call",
                    "results": [{
                        "title": "Source",
                        "url": "https://example.com",
                        "snippet": "Snippet",
                    }],
                }],
            }),
            FakeMetaResponse({"output_text": "Ordinary answer.", "output": []}),
        ]
        client = AIClient(api_key="meta-test", provider="meta")
        client.chat("system", "research", enable_web_search=True)
        self.assertEqual(len(client.last_search_results), 1)
        client.chat("system", "hello", enable_web_search=False)
        self.assertEqual(client.last_search_results, [])

    @patch("agents.requests.post")
    def test_meta_does_not_request_raw_results_when_search_is_disabled(self, post):
        post.return_value = FakeMetaResponse({"output_text": "Ordinary answer.", "output": []})
        client = AIClient(api_key="meta-test", provider="meta")
        client.chat("system", "hello", enable_web_search=False)
        payload = post.call_args.kwargs["json"]
        self.assertNotIn("include", payload)
        self.assertNotIn("tools", payload)


class NovaOrchestratorWebSearchTests(unittest.TestCase):
    class FakeClient:
        def __init__(self):
            self.calls = []
            self.last_citations = []
            self.last_search_results = []
            self.web_search_usage_reported = False
            self.web_search_requests_total = 0
            self.web_search_usage_label = "search requests"
            self.responses = [
                "Plan: research this topic and cite sources.",
                "Research findings.",
                "Analysis.",
                "Reviewed final answer.",
            ]

        def chat(self, system, user, temperature=0.4, enable_web_search=False, allowed_domains=None):
            self.calls.append({
                "system": system,
                "user": user,
                "enable_web_search": enable_web_search,
                "allowed_domains": allowed_domains,
            })
            # Simulate later non-search agents mutating shared client state.
            self.web_search_usage_reported = bool(enable_web_search)
            self.web_search_requests_total = 1 if enable_web_search else 0
            self.last_citations = (
                [{"title": "Official source", "url": "https://iec.ch"}]
                if enable_web_search else []
            )
            self.last_search_results = (
                [{
                    "title": "Retrieved official source",
                    "url": "https://iec.ch",
                    "snippet": "Raw search excerpt.",
                    "cited": True,
                }]
                if enable_web_search else []
            )
            return self.responses[len(self.calls) - 1]

    def test_only_researcher_receives_web_search_tool(self):
        client = self.FakeClient()
        result = NovaOrchestrator(client).run(
            "Research this topic", enable_web_search=True
        )
        self.assertEqual(result["final"], "Reviewed final answer.")
        self.assertEqual(
            [call["enable_web_search"] for call in client.calls],
            [False, True, False, False],
        )
        self.assertIn("You are NOVA Researcher", client.calls[1]["system"])
        self.assertIn("selected provider", client.calls[1]["system"])
        self.assertNotIn("OpenRouter web-search tool", client.calls[1]["system"])
        self.assertEqual(result["research_sources"], [{
            "title": "Official source",
            "url": "https://iec.ch",
        }])
        self.assertEqual(result["research_usage"], {
            "reported": True,
            "requests": 1,
            "label": "search requests",
        })
        self.assertIn("SEARCH ACTIVITY CONFIRMED", result["research_verification_note"])
        self.assertIn("SEARCH ACTIVITY CONFIRMED", client.calls[2]["user"])
        self.assertIn("SEARCH ACTIVITY CONFIRMED", client.calls[3]["user"])


    def test_orchestrator_preserves_raw_research_results_for_ui_audit(self):
        client = self.FakeClient()
        result = NovaOrchestrator(client).run(
            "Research this topic", enable_web_search=True
        )
        self.assertEqual(result["research_results"], [{
            "title": "Retrieved official source",
            "url": "https://iec.ch",
            "snippet": "Raw search excerpt.",
            "cited": True,
        }])

    def test_comparative_mode_uses_existing_researcher_call_and_limits(self):
        client = self.FakeClient()
        result = NovaOrchestrator(client).run(
            "Compare official technical sources",
            enable_web_search=True,
            research_mode="comparative",
        )
        self.assertEqual(len(client.calls), 4)
        self.assertEqual(
            [call["enable_web_search"] for call in client.calls],
            [False, True, False, False],
        )
        self.assertIn("COMPARATIVE SOURCE REVIEW", client.calls[1]["user"])
        self.assertIn("provider-enforced search and fetch limits", client.calls[1]["user"])
        self.assertEqual(result["research_mode"], "comparative")
        self.assertIn("research_mode", client.calls[2]["user"])
        self.assertIn("comparative", client.calls[2]["user"].lower())

    def test_focused_mode_is_the_default(self):
        client = self.FakeClient()
        result = NovaOrchestrator(client).run(
            "Find one official source", enable_web_search=True
        )
        self.assertEqual(result["research_mode"], "focused")
        self.assertIn("FOCUSED LOOKUP", client.calls[1]["user"])
        self.assertNotIn("COMPARATIVE SOURCE REVIEW", client.calls[1]["user"])

    def test_invalid_mode_is_rejected_before_provider_calls(self):
        client = self.FakeClient()
        with self.assertRaisesRegex(ValueError, "focused or comparative"):
            NovaOrchestrator(client).run(
                "Research this topic",
                enable_web_search=True,
                research_mode="unlimited",
            )
        self.assertEqual(client.calls, [])

    def test_researcher_has_no_web_search_when_toggle_is_off(self):
        client = self.FakeClient()
        NovaOrchestrator(client).run("Research this topic", enable_web_search=False)
        self.assertTrue(client.calls)
        self.assertTrue(all(not call["enable_web_search"] for call in client.calls))

    def test_domain_allowlist_is_sent_only_to_researcher(self):
        client = self.FakeClient()
        NovaOrchestrator(client).run(
            "Research official sources",
            enable_web_search=True,
            allowed_domains=["iec.ch"],
        )
        self.assertEqual(
            [call["allowed_domains"] for call in client.calls],
            [None, ["iec.ch"], None, None],
        )


if __name__ == "__main__":
    unittest.main()
