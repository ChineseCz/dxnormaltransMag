import os
import json
import asyncio
from typing import AsyncGenerator, Optional, Dict

import httpx


class ChatService:
    """AI chat streaming service (Qwen + OpenAI-compatible relay)."""

    def __init__(self):
        # Qwen config
        self.qwen_api_key = os.getenv("DASHSCOPE_API_KEY", "")
        self.qwen_url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"
        self.qwen_model = os.getenv("QWEN_MODEL", "qwen-plus")

        # Relay config (OpenAI-compatible)
        self.relay_api_key = os.getenv("RELAY_API_KEY", "")
        self.relay_url = os.getenv("RELAY_API_URL", "https://www.openclaudecode.cn")
        self.relay_model = os.getenv("RELAY_MODEL", "gpt-4o-mini")

        # Default service: qwen | relay
        self.default_service = os.getenv("CHAT_SERVICE", "relay")

        self.system_prompt = (
            "You are a professional electrical-equipment electromagnetic field prediction AI assistant. "
            "You specialize in analyzing electromagnetic field simulation data, model training results, and prediction outcomes. "
            "\n\n"
            "When the user provides platform context (dataset, model, prediction), use it to:\n"
            "1. Understand the specific device type (transformer, reactor, motor, etc.) and field type (magnetic, temperature, stress, etc.)\n"
            "2. Interpret model architecture (DNN/CNN/RF), hyperparameters (PCA dims, hidden layers, optimizer, learning rate, batch size, epochs)\n"
            "3. Analyze prediction results (B_max, B_min, mean, std) in the context of the device's physical characteristics\n"
            "4. Provide domain-specific insights about electromagnetic field distribution, potential issues, and optimization suggestions\n"
            "\n"
            "When context is insufficient, state your assumptions clearly. "
            "Always provide accurate, concise, and actionable answers based on electromagnetic field theory and machine learning best practices."
        )

    async def chat_stream_qwen(
        self,
        messages: list[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ) -> AsyncGenerator[str, None]:
        if not self.qwen_api_key:
            yield json.dumps({"error": "Qwen API key is not configured"}, ensure_ascii=False) + "\n"
            return

        headers = {
            "Authorization": f"Bearer {self.qwen_api_key}",
            "Content-Type": "application/json",
            # DashScope SSE streaming switch (native incremental output)
            "X-DashScope-SSE": "enable",
        }
        formatted_messages = [{"role": "system", "content": self.system_prompt}, *messages]
        payload = {
            "model": self.qwen_model,
            "input": {"messages": formatted_messages},
            "parameters": {
                "temperature": temperature,
                "max_tokens": max_tokens,
                "incremental_output": True,
                "result_format": "message",
            },
        }

        try:
            print("[ai][qwen] start stream request")
            async with httpx.AsyncClient(timeout=60.0) as client:
                async with client.stream("POST", self.qwen_url, headers=headers, json=payload) as response:
                    print(f"[ai][qwen] upstream status={response.status_code}")
                    if response.status_code != 200:
                        detail = (await response.aread()).decode(errors="ignore")
                        print(f"[ai][qwen] upstream error detail={detail[:300]}")
                        yield json.dumps(
                            {"error": f"Qwen API error: {response.status_code}", "detail": detail},
                            ensure_ascii=False,
                        ) + "\n"
                        return

                    first_line_logged = False
                    emitted_chunks = 0
                    async for line in response.aiter_lines():
                        if not first_line_logged:
                            print(f"[ai][qwen] first upstream line={line[:300]}")
                            first_line_logged = True
                        # Compatible with both SSE "data: {...}" and plain JSON lines.
                        data_str = line[5:].strip() if line.startswith("data:") else line.strip()
                        if not data_str or data_str == "[DONE]":
                            continue
                        try:
                            data = json.loads(data_str)
                            choice = (data.get("output", {}).get("choices", [{}]) or [{}])[0]
                            msg = choice.get("message", {})
                            content = msg.get("content", "")
                            if content:
                                # Native streaming path: emit each incremental chunk as-is.
                                # If upstream returns one-shot full text, fallback replay keeps UX streaming.
                                if choice.get("finish_reason") == "stop" and emitted_chunks == 0 and len(content) > 24:
                                    step = 8
                                    for i in range(0, len(content), step):
                                        piece = content[i:i + step]
                                        yield json.dumps({"type": "content", "content": piece}, ensure_ascii=False) + "\n"
                                        emitted_chunks += 1
                                        await asyncio.sleep(0.015)
                                else:
                                    yield json.dumps({"type": "content", "content": content}, ensure_ascii=False) + "\n"
                                    emitted_chunks += 1
                            if choice.get("finish_reason") == "stop":
                                yield json.dumps(
                                    {"type": "done", "usage": data.get("usage", {})}, ensure_ascii=False
                                ) + "\n"
                        except json.JSONDecodeError:
                            continue
        except Exception as e:
            yield json.dumps({"error": f"Request failed: {e}"}, ensure_ascii=False) + "\n"

    async def chat_stream_relay(
        self,
        messages: list[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ) -> AsyncGenerator[str, None]:
        if not self.relay_api_key:
            yield json.dumps({"error": "Relay API key is not configured"}, ensure_ascii=False) + "\n"
            return

        headers = {
            "Authorization": f"Bearer {self.relay_api_key}",
            "Content-Type": "application/json",
        }
        formatted_messages = [{"role": "system", "content": self.system_prompt}, *messages]
        payload = {
            "model": self.relay_model,
            "messages": formatted_messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True,
        }

        try:
            print("[ai][relay] start stream request")
            async with httpx.AsyncClient(timeout=60.0) as client:
                async with client.stream(
                    "POST", f"{self.relay_url}/v1/chat/completions", headers=headers, json=payload
                ) as response:
                    print(f"[ai][relay] upstream status={response.status_code}")
                    if response.status_code != 200:
                        detail = (await response.aread()).decode(errors="ignore")
                        print(f"[ai][relay] upstream error detail={detail[:300]}")
                        yield json.dumps(
                            {"error": f"Relay API error: {response.status_code}", "detail": detail},
                            ensure_ascii=False,
                        ) + "\n"
                        return

                    first_line_logged = False
                    async for line in response.aiter_lines():
                        if not first_line_logged:
                            print(f"[ai][relay] first upstream line={line[:300]}")
                            first_line_logged = True
                        data_str = line[5:].strip() if line.startswith("data:") else line.strip()
                        if not data_str or data_str == "[DONE]":
                            continue
                        try:
                            data = json.loads(data_str)
                            if isinstance(data, dict) and data.get("error"):
                                err = data.get("error") or {}
                                msg = err.get("message") or str(err)
                                yield json.dumps(
                                    {"error": f"Relay upstream error: {msg}", "detail": data},
                                    ensure_ascii=False,
                                ) + "\n"
                                return
                            choice = (data.get("choices") or [{}])[0]
                            delta = choice.get("delta", {})
                            msg = choice.get("message", {})
                            content = delta.get("content", "") or msg.get("content", "")
                            if content:
                                yield json.dumps({"type": "content", "content": content}, ensure_ascii=False) + "\n"
                            if choice.get("finish_reason") in ("stop", "length", "content_filter"):
                                yield json.dumps(
                                    {"type": "done", "usage": data.get("usage", {})}, ensure_ascii=False
                                ) + "\n"
                        except json.JSONDecodeError:
                            print(f"[ai][relay] non-json chunk={data_str[:300]}")
                            if data_str:
                                yield json.dumps({"type": "content", "content": data_str}, ensure_ascii=False) + "\n"
                            continue
        except Exception as e:
            yield json.dumps({"error": f"Request failed: {e}"}, ensure_ascii=False) + "\n"

    async def chat_stream(
        self,
        messages: list[Dict[str, str]],
        service: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ) -> AsyncGenerator[str, None]:
        service_name = service or self.default_service
        if service_name == "qwen":
            async for chunk in self.chat_stream_qwen(messages, temperature, max_tokens):
                yield chunk
        elif service_name == "relay":
            async for chunk in self.chat_stream_relay(messages, temperature, max_tokens):
                yield chunk
        else:
            yield json.dumps({"error": f"Unknown service: {service_name}"}, ensure_ascii=False) + "\n"
