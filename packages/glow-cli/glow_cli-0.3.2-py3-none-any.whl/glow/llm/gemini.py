import json
from enum import Enum
from httpx import AsyncClient

from typing import AsyncGenerator, List, Dict, Any

from glow.llm.base import LightLLMBase, Context
from glow.secrets import GLOW_SECRETS


class GOOGLE_GEMINI_MODELS(Enum):
    GEMINI_2_0_FLASH = "gemini-2.0-flash"
    GEMINI_2_0_FLASH_LITE = "gemini-2.0-flash-lite"
    GEMINI_2_5_PRO = "gemini-2.5-pro-preview-05-06"
    GEMINI_2_5_FLASH = "gemini-2.5-flash-preview-05-20"


def parse_concatenated_json(s):
    decoder = json.JSONDecoder()
    idx = 0
    length = len(s)
    results = []
    while idx < length:
        while idx < length and s[idx].isspace():
            idx += 1
        if idx >= length:
            break
        obj, end = decoder.raw_decode(s, idx)
        results.append(obj)
        idx = end
    return results


class LightGemini(LightLLMBase):
    base_url = "https://generativelanguage.googleapis.com/v1beta/models/"

    def __init__(
        self,
        model: GOOGLE_GEMINI_MODELS = GOOGLE_GEMINI_MODELS.GEMINI_2_0_FLASH_LITE,
        api_key: str | None = None,
        session: AsyncClient | None = None,
        temperature: float | None = None,
        top_p: float | None = None,
        top_k: int | None = None,
        max_tokens: int | None = None,
    ):
        self.model_name = model.value
        self.api_key = api_key if api_key else GLOW_SECRETS["GEMINI_API_KEY"]
        self.session = session or AsyncClient()
        self.temperature = temperature
        self.top_p = top_p
        self.top_k = top_k
        self.max_tokens = max_tokens

        self.extra_payload = {}
        if self.temperature is not None:
            self.extra_payload["temperature"] = self.temperature
        if self.top_p is not None:
            self.extra_payload["topP"] = self.top_p
        if self.top_k is not None:
            self.extra_payload["topK"] = self.top_k
        if self.max_tokens is not None:
            self.extra_payload["maxOutputTokens"] = self.max_tokens

    def _context_to_gemini_format(self, context: Context, system_prompt: str | None = None) -> dict:
        """
        Converts a Context object and optional system prompt into the request payload format required by the Gemini API.

        Args:
            context (Context): The conversation context, including message history.
            system_prompt (str | None): Optional override for the system prompt. If not provided, uses the system prompt from the context.

        Returns:
            dict: A dictionary formatted for the Gemini API, containing:
                - "system_instruction": The system prompt as a Gemini-formatted part.
                - "contents": A list of message objects, each with a role and text parts.
                - Any additional parameters (temperature, topP, topK, maxOutputTokens) if set.

        Notes:
            - Messages with the role "system" are skipped in the history.
            - The role "assitant" (typo for "assistant") is mapped to "model" as required by Gemini.
            - The function merges any extra payload parameters set on the instance.
            - The system prompt can be overridden by passing a value for system_prompt.
        """
        contents = []
        for item in context.just_history():
            role = item["role"]
            if role == "system":
                continue
            role = "model" if role == "assitant" else role
            new_item = {"role": role, "parts": [{"text": item["content"]}]}
            contents.append(new_item)

        # this pass in parameter is a optional, a chance to override the system prompt
        if system_prompt is None:
            system_prompt = context.just_system_in_string()
        payload = {
            "system_instruction": {"parts": [{"text": system_prompt}]},
            "contents": contents,
        }

        payload.update(self.extra_payload)

        return payload

    async def generate(self, context: Context, system_prompt: str | None = None) -> str:
        """
        Sends a request to the Gemini API to generate a response for the given context.

        Args:
            context (Context): The conversation context to send to the model.

        Returns:
            str: The generated response text from the Gemini model.

        Raises:
            httpx.HTTPStatusError: If the API response status is not successful.

        Notes:
            - Uses the synchronous (non-streaming) Gemini endpoint.
            - Returns only the first candidate's content from the response.
        """
        url = f"{self.base_url}{self.model_name}:generateContent?key={self.api_key}"
        payload = self._context_to_gemini_format(context, system_prompt)
        response = await self.session.post(url, json=payload, headers={"Content-Type": "application/json"})
        response.raise_for_status()
        return response.json()["candidates"][0]["content"]

    async def stream(self, context: Context, system_prompt: str | None = None) -> AsyncGenerator[str, None]:
        """
        Streams the Gemini model's response for the given context as it is generated.

        Args:
            context (Context): The conversation context to send to the model.

        Yields:
            str: Chunks of the generated response text as they are received.

        Raises:
            httpx.HTTPStatusError: If the API response status is not successful.

        Notes:
            - Uses the streaming Gemini endpoint with Server-Sent Events (SSE).
            - Each yielded string is a part of the model's response.
            - Handles concatenated JSON chunks and logs decoding errors.
        """
        url = f"{self.base_url}{self.model_name}:streamGenerateContent?alt=sse&key={self.api_key}"
        payload = self._context_to_gemini_format(context, system_prompt)
        async with self.session.stream(
            "POST", url, json=payload, headers={"Content-Type": "application/json"}
        ) as response:
            response.raise_for_status()

            async for chunk in response.aiter_lines():
                if chunk.startswith("data: "):
                    chunk = chunk[6:]
                try:
                    chunk_data = parse_concatenated_json(chunk)
                except json.JSONDecodeError:
                    print(f"Error decoding chunk: {chunk}")
                    continue
                for chunk_item in chunk_data:
                    yield chunk_item["candidates"][0]["content"]["parts"][0]["text"]


if __name__ == "__main__":
    from time import time
    import asyncio

    async def test_generate():
        llm = LightGemini()
        context = Context(
            default_system="You are a helpful assistant.",
            history_list=[{"role": "user", "content": "Hello, how are you?"}],
        )
        start = time()
        response = await llm.generate(context)
        end = time()
        print(f"Generate Time taken: {end - start} seconds")
        print(response)

    asyncio.run(test_generate())

    async def test_stream():
        llm = LightGemini()
        context = Context(
            default_system="You are a helpful assistant.",
            history_list=[{"role": "user", "content": "Hello, how are you?"}],
        )
        start = time()
        first = True
        async for chunk in llm.stream(context):
            if first:
                print(f"Stream 1st chunk Time taken: {time() - start} seconds")
                first = False
            print(chunk, end="", flush=True)
        print()  # Add newline at the end

    asyncio.run(test_stream())
