import asyncio
from typing import Any, Dict, Optional

from glow.colors import cprint
from glow.configs import GLOW_CONFIGS
from glow.llm.base import Context
from glow.llm.openai import LightOpenAI
from glow.llm.gemini import LightGemini


async def run_llm_async(question: str, system_content: Optional[str] = None) -> None:
    llm_provider = GLOW_CONFIGS["GLOW_LLM"]

    if llm_provider == "openai":
        model = LightOpenAI()
    elif llm_provider == "gemini":
        model = LightGemini()
    else:
        cprint(f"llm provider {llm_provider} not supported for now", "yellow")
        return

    context = Context(
        default_system=system_content or "",
        history_list=[
            {"role": "user", "content": question},
        ],
    )

    if hasattr(model, "stream"):
        try:
            async for token in model.stream(context=context):
                print(token, end="")
        except KeyboardInterrupt:
            cprint("\n=========== generation interrupted by user ===========", "yellow")
        except Exception as e:
            raise e
    else:
        generated_text = await model.generate(context=context)
        print(generated_text)


def run_llm(question: str, system_content: Optional[str] = None) -> None:
    asyncio.run(run_llm_async(question, system_content))
