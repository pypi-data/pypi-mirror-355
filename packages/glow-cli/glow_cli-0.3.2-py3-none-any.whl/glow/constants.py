import os
from pathlib import Path

# the ASCII art for the logo
ASCII_ART = """
   ________    ____ _       __
  / ____/ /   / __ \ |     / /
 / / __/ /   / / / / | /| / /
/ /_/ / /___/ /_/ /| |/ |/ /
\____/_____/\____/ |__/|__/
"""
GLOW_CONF: Path = Path.home() / ".glow"
GLOW_CONF.mkdir(exist_ok=True, parents=True)
GLOW_COMMANDS = GLOW_CONF / "commands"
GLOW_COMMANDS.mkdir(exist_ok=True, parents=True)
GLOW_SECRETS_FILE = GLOW_CONF / "secrets" / "secrets.yml"
GLOW_CONFIGS_FILE = GLOW_CONF / "configs" / "configs.yml"


LLM_TEMPLATE = """
   based on {question}, generate bash script that we can run in {system}.
   Please answer with the script only.
   start the script with: 🍔🍔🍔
   end the script with: 🍟🍟🍟
   """

EXAMPLE_COMMAND = """
description: this is an example command
command: |
  echo "hello ,{people}"
inputs:
  people:
    type: text
    default: world
"""


GLOW_CONFIG_OPTIONS = {
    "GLOW_LLM": ["openai", "anthropic"],
    "OPENAI_MODEL": [
        "gpt-3.5-turbo-1106",
        "gpt-3.5-turbo",
        "gpt-3.5-turbo-16k",
        "gpt-4",
        "gpt-4-32k",
        "gpt-4-1106-preview",
    ],
    "ANTHROPIC_MODEL": [
        "claude-2.1",
        "claude-2",
        "claude-instant-1",
        "claude-instant-1.2",
    ],
}
