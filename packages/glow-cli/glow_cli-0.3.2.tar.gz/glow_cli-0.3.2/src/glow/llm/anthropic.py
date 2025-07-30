from glow.colors import cprint
from glow.configs import GLOW_CONFIGS
from glow.secrets import GLOW_SECRETS
from important.llmsdk.anthropic import ChatClaude


def build_anthropic_llm() -> ChatClaude:
    ANTHROPIC_API_KEY = GLOW_SECRETS["ANTHROPIC_API_KEY"]
    ANTHROPIC_MODEL = GLOW_CONFIGS["ANTHROPIC_MODEL"]

    llm = ChatClaude(
        model_name=ANTHROPIC_MODEL,
        api_key=ANTHROPIC_API_KEY,
    )
    return llm
