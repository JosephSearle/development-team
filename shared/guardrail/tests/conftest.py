import pytest
from dev_team_guardrail.client import GuardrailClient


@pytest.fixture()
def guardrail_url() -> str:
    return "http://llama-guard-test:8080"


@pytest.fixture()
def client(guardrail_url: str) -> GuardrailClient:
    return GuardrailClient(endpoint=guardrail_url)
