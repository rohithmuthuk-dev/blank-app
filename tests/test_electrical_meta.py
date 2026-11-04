import unittest
from unittest.mock import patch

from agents import AIClient, AIProviderError
from electrical_domain import ELECTRICAL_ENGINEERING_GUIDANCE, build_workbench_prompt


class FakeMetaResponse:
    def __init__(self, data):
        self.data = data
    def raise_for_status(self):
        return None
    def json(self):
        return self.data


class MetaModelApiTests(unittest.TestCase):
    @patch("agents.requests.post")
    def test_meta_uses_responses_api_and_muse_spark(self, post):
        post.return_value = FakeMetaResponse({"output_text": "CT test procedure"})
        client = AIClient(api_key="meta-test", provider="meta")
        answer = client.chat("system instructions", "Explain CT knee point test")
        self.assertEqual(answer, "CT test procedure")
        args = post.call_args
        self.assertEqual(args.args[0], "https://api.meta.ai/v1/responses")
        self.assertEqual(args.kwargs["json"]["model"], "muse-spark-1.3")
        self.assertEqual(args.kwargs["json"]["instructions"], "system instructions")

    @patch("agents.requests.post")
    def test_meta_search_grounding_tool_is_opt_in(self, post):
        post.return_value = FakeMetaResponse({
            "output_text": "IEC reference overview",
            "output": [{"type": "web_search_call"}],
        })
        client = AIClient(api_key="meta-test", provider="meta")
        client.chat("system", "Find current official IEC information", enable_web_search=True)
        payload = post.call_args.kwargs["json"]
        self.assertEqual(payload["tools"][0]["type"], "web_search")
        self.assertTrue(client.web_search_usage_reported)
        self.assertEqual(client.web_search_requests_total, 1)

    @patch("agents.requests.post")
    def test_meta_citations_are_rendered(self, post):
        post.return_value = FakeMetaResponse({
            "output": [{
                "type": "message",
                "content": [{
                    "type": "output_text",
                    "text": "Sourced answer",
                    "annotations": [{
                        "type": "url_citation",
                        "url": "https://example.com/standard",
                        "title": "Official source",
                    }],
                }],
            }],
        })
        answer = AIClient(api_key="meta-test", provider="meta").chat("system", "question")
        self.assertIn("[Official source](<https://example.com/standard>)", answer)
        self.assertIn("Sourced answer", answer)

    def test_meta_missing_key_has_actionable_error(self):
        client = AIClient(api_key="", provider="meta")
        with self.assertRaisesRegex(AIProviderError, "MODEL_API_KEY"):
            client.chat("system", "hello")


class ElectricalDomainTests(unittest.TestCase):
    def test_workbench_prompt_includes_selected_context(self):
        prompt = build_workbench_prompt(
            "CT (Current Transformer)", "Step-by-step test procedure",
            "Site testing / commissioning", "220 kV", "Siemens 800/1 A",
            "Need knee point and winding resistance test"
        )
        self.assertIn("220 kV", prompt)
        self.assertIn("Siemens 800/1 A", prompt)
        self.assertIn("knee point", prompt)

    def test_safety_and_standards_guardrails_exist(self):
        self.assertIn("Never invent IEC", ELECTRICAL_ENGINEERING_GUIDANCE)
        self.assertIn("energized CT secondary", ELECTRICAL_ENGINEERING_GUIDANCE)
        self.assertIn("TBC", ELECTRICAL_ENGINEERING_GUIDANCE)


if __name__ == "__main__":
    unittest.main()
