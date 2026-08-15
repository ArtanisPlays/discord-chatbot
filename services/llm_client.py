import os
import asyncio
import json
import logging
import aiohttp

logger = logging.getLogger("LLMClient")


class LLMClient:
    """Async client for OpenAI-compatible chat completion endpoints.

    Works with OpenAI, OpenRouter, Groq, Together, Gemini (OpenAI-compat mode),
    local llama.cpp / Ollama servers, or any API exposing a /chat/completions
    style endpoint. If no endpoint is configured, `generate_reply` returns None
    so the caller can fall back to rule-based replies.
    """

    def __init__(self):
        self.endpoint = os.getenv("CHAT_API_URL", "").strip()
        self.api_key = os.getenv("CHAT_API_KEY", "").strip()
        self.model = os.getenv("CHAT_API_MODEL", "").strip() or "gpt-4o-mini"
        self.system_prompt = os.getenv(
            "CHAT_API_SYSTEM_PROMPT",
            "Kamu adalah Garapizza, AI yang santai dan asyik buat diajak ngobrol. "
            "Jawab dengan gaya santai, natural, dan hangat seperti ngobrol sama teman. "
            "Pakai bahasa yang sama dengan user. Tetap ringkas dan nggak bertele-tele.",
        )
        try:
            # Max idle time between streamed chunks (not a total request cap).
            # As long as data keeps arriving, the request may run as long as
            # the model needs to think, so slow responses are not cut off.
            self.timeout = int(os.getenv("CHAT_API_TIMEOUT", "120"))
        except ValueError:
            self.timeout = 120
        self.enabled = bool(self.endpoint)

    async def generate_reply(self, user_message: str, user_name: str, history: list = None,
                             model: str | None = None) -> str | None:
        """Send a chat completion request and return the reply text.

        Returns None when the API is not configured or the request fails,
        so the caller can fall back to local rule-based responses.
        """
        if not self.enabled:
            return None

        messages = [{"role": "system", "content": self.system_prompt}]
        if user_name:
            messages[0]["content"] += f"\nYou are chatting with a user named {user_name}."
        if history:
            messages.extend(history)
        messages.append({"role": "user", "content": user_message})

        payload = {
            "model": model or self.model,
            "messages": messages,
            "stream": True,
            "temperature": 0.7,
            "max_tokens": 1024,
        }

        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        # No overall cap (streaming may take a long time); fail fast on connect
        # problems, and cancel only if the API goes silent for `timeout` seconds.
        timeout = aiohttp.ClientTimeout(
            total=None,
            sock_connect=15,
            sock_read=self.timeout,
        )
        try:
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(self.endpoint, json=payload, headers=headers) as resp:
                    if resp.status != 200:
                        body = await resp.text()
                        logger.error(f"Chat API returned {resp.status}: {body[:500]}")
                        return None
                    content_type = resp.headers.get("Content-Type", "")
                    if "text/event-stream" in content_type:
                        return await self._consume_stream(resp)
                    data = await resp.json()
        except asyncio.TimeoutError:
            logger.error(f"Chat API sent no data for {self.timeout}s; gave up waiting")
            return None
        except aiohttp.ClientError as e:
            logger.error(f"Chat API request failed: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected Chat API error: {e}")
            return None

        return self._extract_reply(data)

    @staticmethod
    async def _consume_stream(resp: aiohttp.ClientResponse) -> str | None:
        """Consume a Server-Sent-Events response and join the streamed text.

        Each event is an OpenAI-compatible `chat.completion.chunk`:
        `{"choices": [{"delta": {"content": "..."}}]}`. Reasoning-only chunks
        (`delta.reasoning_content`) are skipped.
        """
        parts = []
        async for line in resp.content:
            if not line:
                continue
            line = line.decode("utf-8", errors="replace").strip()
            if not line.startswith("data:"):
                continue
            data = line[len("data:"):].strip()
            if data == "[DONE]":
                break
            try:
                chunk = json.loads(data)
            except json.JSONDecodeError:
                continue
            try:
                delta = chunk["choices"][0]["delta"]
            except (KeyError, IndexError, TypeError):
                continue
            content = delta.get("content")
            if isinstance(content, str) and content:
                parts.append(content)
        reply = "".join(parts).strip()
        return reply or None

    @staticmethod
    def _models_url(endpoint: str) -> str | None:
        """Derive the GET /models URL from the chat completions endpoint."""
        if not endpoint:
            return None
        suffix = "/chat/completions"
        if endpoint.rstrip("/").endswith(suffix):
            return endpoint.rstrip("/")[: -len(suffix)] + "/models"
        base = endpoint.rstrip("/").rsplit("/", 1)[0]
        return base + "/models"

    async def fetch_models(self) -> list[dict]:
        """Fetch available models from the API's /models endpoint.

        Returns a list of {"id": ..., "name": ...} dicts, or [] on failure.
        """
        url = self._models_url(self.endpoint)
        if not url:
            return []

        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=15)) as session:
                async with session.get(url, headers=headers) as resp:
                    if resp.status != 200:
                        body = await resp.text()
                        logger.error(f"Models API returned {resp.status}: {body[:300]}")
                        return []
                    data = await resp.json()
        except (asyncio.TimeoutError, aiohttp.ClientError) as e:
            logger.error(f"Models API request failed: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected Models API error: {e}")
            return []

        return self._parse_models(data)

    @staticmethod
    def _parse_models(data) -> list[dict]:
        """Extract model {id, name} entries from common /models response shapes."""
        # Some APIs return a bare list, others wrap it as {"data": [...]}
        raw = data.get("data") if isinstance(data, dict) else data
        models = []
        if isinstance(raw, list):
            for item in raw:
                if isinstance(item, dict) and item.get("id"):
                    models.append({
                        "id": item["id"],
                        "name": item.get("name") or item["id"],
                    })
        return models

    @staticmethod
    def _extract_reply(data: dict) -> str | None:
        """Extract the reply text from common API response shapes."""
        try:
            content = data["choices"][0]["message"]["content"]
            if content:
                return content.strip()
        except (KeyError, IndexError, TypeError):
            pass

        # Tolerant fallbacks for other response shapes
        for key in ("response", "content", "text", "output", "completion", "reply"):
            value = data.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()

        if isinstance(data.get("choices"), list):
            for choice in data["choices"]:
                for key in ("text", "content"):
                    value = choice.get(key)
                    if isinstance(value, str) and value.strip():
                        return value.strip()
                    if isinstance(value, dict):
                        value = value.get("content")
                        if isinstance(value, str) and value.strip():
                            return value.strip()

        logger.error(f"Could not parse Chat API response: {str(data)[:500]}")
        return None
