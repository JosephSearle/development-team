from __future__ import annotations

import dataclasses

import httpx


class GuardrailUnavailableError(Exception):
    """Raised when the Llama-Guard vLLM endpoint is unreachable or returns a non-2xx response."""


@dataclasses.dataclass
class GuardrailResult:
    passed: bool
    category: str | None  # e.g. "S2"; None when passed=True


class GuardrailClient:
    def __init__(
        self,
        endpoint: str,
        model: str = "meta-llama/Llama-Guard-3-8B",
        timeout: float = 10.0,
    ) -> None:
        self._endpoint = endpoint
        self._model = model
        self._timeout = timeout

    async def screen(self, text: str) -> GuardrailResult:
        payload = {
            "model": self._model,
            "messages": [{"role": "user", "content": text}],
            "max_tokens": 20,
        }
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as http:
                response = await http.post(
                    f"{self._endpoint}/v1/chat/completions",
                    json=payload,
                )
        except (httpx.ConnectError, httpx.TimeoutException) as exc:
            raise GuardrailUnavailableError(str(exc)) from exc

        if response.status_code >= 300:
            raise GuardrailUnavailableError(
                f"Guardrail endpoint returned HTTP {response.status_code}"
            )

        content: str = response.json()["choices"][0]["message"]["content"].strip()

        if content == "safe":
            return GuardrailResult(passed=True, category=None)

        # Format: "unsafe\n<category>"
        parts = content.split("\n", maxsplit=1)
        category = parts[1].strip() if len(parts) > 1 else None
        return GuardrailResult(passed=False, category=category)
