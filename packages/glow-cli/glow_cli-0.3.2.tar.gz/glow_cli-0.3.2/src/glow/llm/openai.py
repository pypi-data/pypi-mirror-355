import asyncio
from enum import Enum
from httpx import AsyncClient
import json
from typing import AsyncGenerator

from glow.llm.base import Context, LightLLMBase
from glow.secrets import GLOW_SECRETS


class OPEN_AI_MDOELS(Enum):
    GPT_4_1_NANO = "gpt-4.1-nano-2025-04-14"
    GPT_4_1_MINI = "gpt-4.1-mini-2025-04-14"
    GPT_4_1 = "gpt-4.1-2025-04-14"


class LightOpenAI(LightLLMBase):
    """
    OpenAI LLM Very Light Weight Client
    Does async generation or streaming
    """

    api_endpoint = "https://api.openai.com/v1/chat/completions"

    def __init__(
        self,
        model: OPEN_AI_MDOELS = OPEN_AI_MDOELS.GPT_4_1_NANO,
        api_key: str | None = None,
        session: AsyncClient | None = None,
        json_object: bool = False,
        temperature: float | None = None,
    ):
        self._model_name: str = model.value
        self._api_key: str = api_key or GLOW_SECRETS["OPENAI_API_KEY"]
        self._session: AsyncClient = session or AsyncClient()
        self._json_object: bool = json_object
        self._temperature: float | None = temperature

    async def prepare_payload(
        self,
        context: Context,
        system_prompt: str | None = None,
        stream: bool = False,
    ) -> dict:
        """
        Prepare the payload for the OpenAI API
        """
        if system_prompt is None:
            messages = await context.to_messages()
        else:
            messages = [{"role": "system", "content": system_prompt}] + context.just_history()

        payload = {
            "model": self._model_name,
            "messages": messages,
        }

        if stream:
            payload["stream"] = True

        if self._json_object:
            payload["response_format"] = {"type": "json_object"}

        if self._temperature is not None:
            payload["temperature"] = self._temperature

        return payload

    async def generate(
        self,
        context: Context,
        system_prompt: str | None = None,
    ) -> str:
        """
        Generate a response from the LLM
        1 shot generation, not streaming
        """
        payload = await self.prepare_payload(context, system_prompt, stream=False)

        response = await self._session.post(
            self.api_endpoint,
            json=payload,
            headers={"Authorization": f"Bearer {self._api_key}"},
        )
        response.raise_for_status()
        res_data = response.json()

        return res_data["choices"][0]["message"]["content"]

    async def stream(
        self,
        context: Context,
        system_prompt: str | None = None,
    ) -> AsyncGenerator[str, None]:
        """
        Stream a response from the LLM
        Streaming generation, get as more tokens as soon as they are available
        """
        payload = await self.prepare_payload(context, system_prompt, stream=True)

        async with self._session.stream(
            "POST",
            self.api_endpoint,
            json=payload,
            headers={"Authorization": f"Bearer {self._api_key}"},
        ) as response:
            # error handling if response is not 200
            response.raise_for_status()
            async for chunk in response.aiter_lines():
                if chunk.startswith("data: "):
                    chunk = chunk[6:]
                    if chunk == "[DONE]":
                        break
                    chunk = json.loads(chunk)
                    delta = chunk["choices"][0]["delta"]
                    if "content" in delta:
                        yield delta["content"]


if __name__ == "__main__":
    from time import time

    async def test_stream():
        llm = LightOpenAI()
        context = Context(
            default_system="You are a helpful assistant.",
            history_list=[{"role": "user", "content": "Hello, how are you?"}],
        )
        start = time()
        first = True
        async for chunk in llm.stream(context):
            if first:
                print(f"Time taken: {time() - start} seconds")
                first = False
            print(chunk, end="", flush=True)

        end = time()
        print(f"Async Stream Time taken: {end - start} seconds")

    asyncio.run(test_stream())

    async def test_generate():
        llm = LightOpenAI()
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
