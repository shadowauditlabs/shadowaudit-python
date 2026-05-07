"""Tests for cloud client with graceful offline fallback."""


from shadowaudit.cloud.client import CloudClient


class TestCloudClientOfflineMode:
    """Cloud client without API key: always local-only."""

    def test_offline_mode_without_key(self):
        client = CloudClient()
        assert client.offline_mode is True
        assert client.last_error is None

    def test_fallback_to_local_delta(self):
        client = CloudClient()
        threshold = client.get_threshold(K=0.5, V=0.1, delta=0.3)
        assert threshold == 0.3
        assert client.last_error is None

    def test_evaluate_fire_and_forget_offline(self):
        client = CloudClient()
        result = {"passed": True, "metadata": {"payload_hash": "abc123"}}
        assert client.evaluate(agent_id="a", task_context="t", risk_category="c", payload={}, local_result=result) is result


class TestCloudClientWithKey:
    """Cloud client with API key but no real server: should fall back."""

    def test_not_offline_with_key(self):
        client = CloudClient(api_key="sk_test_123")
        assert client.offline_mode is False

    def test_fallback_on_bad_url(self):
        client = CloudClient(api_key="sk_test_123", base_url="http://localhost:99999/invalid")
        threshold = client.get_threshold(K=0.5, V=0.1, delta=0.3)
        assert threshold == 0.3
        assert client.last_error is not None

    def test_custom_timeout(self):
        client = CloudClient(api_key="sk_test_123", timeout=0.001)
        assert client._timeout == 0.001

    def test_evaluate_fire_and_forget_with_key(self):
        client = CloudClient(api_key="sk_test_123", base_url="http://localhost:99999/invalid")
        result = {"passed": False, "metadata": {"payload_hash": "abc123"}}
        assert client.evaluate(agent_id="a", task_context="t", risk_category="c", payload={}, local_result=result) is result


class TestCloudClientFromEnv:
    """API key from environment variable."""

    def test_api_key_from_env(self, monkeypatch):
        monkeypatch.setenv("SHADOWAUDIT_API_KEY", "sk_env_123")
        client = CloudClient()
        assert not client.offline_mode
        assert client._api_key == "sk_env_123"

    def test_base_url_from_env(self, monkeypatch):
        monkeypatch.setenv("SHADOWAUDIT_BASE_URL", "https://custom.example.com/v2")
        client = CloudClient()
        assert client._base_url == "https://custom.example.com/v2"
