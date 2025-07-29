"""Agent module: defines the core LLM agent with tool and conversation handling."""

import time
from openai import OpenAI
from janito.agent.conversation import ConversationHandler
from janito.agent.conversation_exceptions import ProviderError
from janito.agent.llm_conversation_history import LLMConversationHistory


class Agent:
    """Agent capable of handling conversations and tool calls."""

    REFERER = "www.janito.dev"
    TITLE = "Janito"

    def __init__(
        self,
        api_key: str,
        model: str = None,
        system_prompt_template: str | None = None,
        verbose_tools: bool = False,
        base_url: str = None,
        azure_openai_api_version: str = "2023-05-15",
        use_azure_openai: bool = False,
    ):
        """
        Initialize Agent.

        Args:
            api_key: API key for OpenAI-compatible service.
            model: Model name to use.
            system_prompt_template: Optional system prompt override.
            verbose_tools: Enable verbose tool call logging.
            base_url: API base URL.
            azure_openai_api_version: Azure OpenAI API version (default: "2023-05-15").
            use_azure_openai: Whether to use Azure OpenAI client (default: False).
        """
        self.api_key = api_key
        self.model = model
        self.system_prompt_template = system_prompt_template
        if use_azure_openai:
            # Import inside conditional to avoid requiring AzureOpenAI unless needed
            from openai import AzureOpenAI

            if base_url:
                self.client = AzureOpenAI(
                    api_key=api_key,
                    azure_endpoint=base_url,
                    api_version=azure_openai_api_version,
                )
            else:
                self.client = AzureOpenAI(
                    api_key=api_key,
                    api_version=azure_openai_api_version,
                )
        else:
            if base_url:
                self.client = OpenAI(
                    base_url=base_url,
                    api_key=api_key,
                    default_headers={
                        "HTTP-Referer": self.REFERER,
                        "X-Title": self.TITLE,
                    },
                )
            else:
                self.client = OpenAI(
                    api_key=api_key,
                    default_headers={
                        "HTTP-Referer": self.REFERER,
                        "X-Title": self.TITLE,
                    },
                )

        self.conversation_handler = ConversationHandler(
            self.client,
            self.model,
        )

    @property
    def usage_history(self):
        return self.conversation_handler.usage_history

    def chat(
        self,
        messages=None,
        message_handler=None,
        spinner=False,
        max_tokens=None,
        max_rounds=100,
        tool_user=False,
    ):
        """
        Start a chat conversation with the agent.

        Args:
            messages: LLMConversationHistory instance or None.
            message_handler: Optional handler for event messages.
            spinner: Show spinner during request.
            max_tokens: Max tokens for completion.
            max_rounds: Max conversation rounds.
        Returns:
            dict with 'content', 'usage', and 'usage_history'.
        """
        from janito.agent.runtime_config import runtime_config

        if messages is None:
            messages = LLMConversationHistory()
        elif not isinstance(messages, LLMConversationHistory):
            raise TypeError(
                "Agent.chat expects a LLMConversationHistory instance or None."
            )

        max_retries = 5
        for attempt in range(1, max_retries + 1):
            try:
                return self.conversation_handler.handle_conversation(
                    messages,
                    max_rounds=max_rounds,
                    message_handler=message_handler,
                    verbose_response=runtime_config.get("verbose_response", False),
                    spinner=spinner,
                    max_tokens=max_tokens,
                    verbose_events=runtime_config.get("verbose_events", False),
                    tool_user=tool_user,
                )
            except ProviderError as e:
                error_data = getattr(e, "error_data", {}) or {}
                code = error_data.get("code", "")
                # Retry only on 5xx errors
                if isinstance(code, int) and 500 <= code < 600:
                    pass
                elif (
                    isinstance(code, str) and code.isdigit() and 500 <= int(code) < 600
                ):
                    code = int(code)
                else:
                    raise

                if attempt < max_retries:
                    print(
                        f"ProviderError with 5xx code encountered (attempt {attempt}/{max_retries}). Retrying in 5 seconds..."
                    )
                    time.sleep(5)
                else:
                    print("Max retries reached. Raising error.")
                    raise

                raise
