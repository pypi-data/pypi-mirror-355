from typing import AsyncGenerator, List


class Context:
    """
    Chat History management
    """

    def __init__(
        self,
        default_system: str,
        history_list: list[dict],
    ):
        """
        Initialize the context with a default system prompt and a history list.
        """
        self._history = history_list
        self._default_system = default_system

    async def to_messages(self):
        return self._history

    async def update_from_context(self, context: List[dict]):
        self._history = context

    def set_system(self, system_prompt: str):
        """
        Set the system prompt to the context.
        """
        for line in self._history:
            if line["role"] == "system":
                line["content"] = system_prompt
                break
        else:
            self._history.insert(0, {"role": "system", "content": system_prompt})

    def just_system(self):
        """
        Return the system prompt without the history.
        """
        return [line for line in self._history if line["role"] == "system"]

    def just_history(self):
        """
        Return the history without the system prompt.
        """
        return [line for line in self._history if line["role"] != "system"]

    def just_system_in_string(self) -> str:
        """
        Return the system prompt as a string.
        """
        system_messages = self.just_system()
        if system_messages:
            return system_messages[0]["content"]
        return self._default_system

    def just_history_in_string(self) -> str:
        """
        Return the history as a formatted string.
        """
        history_lines = []
        for message in self.just_history():
            role = message["role"]
            content = message["content"]
            history_lines.append(f"{role}: {content}")
        return "\n".join(history_lines)


class LightLLMBase:
    """
    Base class for all LLM clients (light weight version)

    The point of these implementation is to provide a light weight LLM python clients
        that doesn't reply on official python SDK to interact with LLM.

    Less dependencies, less import, more controllable speed and latency.
    """

    async def generate(
        self,
        context: Context,
        system_prompt: str | None = None,
    ): ...

    async def stream(
        self,
        context: Context,
        system_prompt: str | None = None,
    ) -> AsyncGenerator[str, None]: ...
