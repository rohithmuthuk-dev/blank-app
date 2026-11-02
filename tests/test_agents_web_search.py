import unittest
from unittest.mock import patch

from agents import AIClient, AIProviderError


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


class AIClientWebSearchTests(unittest.TestCase):
    def setUp(self):
        self.client = AIClient(api_key="test-key", model="test-model")

    @patch("agents.requests.post")
    def test_web_search_is_disabled_by_default(self, post):
        post.return_value = FakeResponse({"content": "Hello"})
        self.client.chat("system", "hello")
        payload = post.call_args.kwargs["json"]
        self.assertNotIn("tools", payload)
        self.assertNotIn("stop_server_tools_when", payload)

    @patch("agents.requests.post")
    def test_web_search_has_a_two_call_limit(self, post):
        post.return_value = FakeResponse({"content": "Research result"})
        self.client.chat("system", "research this", enable_web_search=True)
        payload = post.call_args.kwargs["json"]
        self.assertEqual(
            payload["stop_server_tools_when"],
            [{"type": "step_count_is", "step_count": 2}],
        )
        self.assertEqual(payload["tools"][0]["parameters"]["max_uses"], 2)
        self.assertEqual(payload["tools"][0]["parameters"]["max_total_results"], 10)

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
        self.assertIn("[Example article](https://example.com/article)", answer)

    @patch("agents.requests.post")
    def test_server_tool_usage_is_recorded(self, post):
        post.return_value = FakeResponse(
            {"content": "Searched answer"},
            usage={"server_tool_use": {"web_search_requests": 2}},
        )
        self.client.chat("system", "research", enable_web_search=True)
        self.assertTrue(self.client.web_search_usage_reported)
        self.assertEqual(self.client.web_search_requests_total, 2)

    @patch("agents.requests.post")
    def test_missing_server_tool_usage_is_not_reported_as_zero(self, post):
        post.return_value = FakeResponse({"content": "Answer"})
        self.client.chat("system", "research", enable_web_search=True)
        self.assertFalse(self.client.web_search_usage_reported)

    def test_missing_key_fails_before_network_request(self):
        client = AIClient(api_key="")
        with self.assertRaises(AIProviderError):
            client.chat("system", "hello")


if __name__ == "__main__":
    unittest.main()
