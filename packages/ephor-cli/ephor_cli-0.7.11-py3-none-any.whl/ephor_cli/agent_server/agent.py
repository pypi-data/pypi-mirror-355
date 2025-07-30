import logging
from contextlib import asynccontextmanager
from typing import AsyncIterable, Union, Optional

from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_aws import ChatBedrock
from langchain_core.messages import (
    BaseMessage,
    HumanMessage,
    AIMessageChunk,
    ToolMessageChunk,
)
from ephor_cli.mcp_adapters.client import MultiServerMCPClient
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent
from ephor_cli.types.agent import MCPServerConfig, HiveInstance
from ephor_cli.types.llm import Model, LLMProvider
from ephor_cli.constant import MCP_SERVER_URL

logger = logging.getLogger(__name__)


def _create_llm_instance(model: Model):
    """Create the appropriate LLM instance based on the model provider."""
    print(f"Creating LLM instance for model: {model.name}, provider: {model.provider}")
    if model.provider == LLMProvider.ANTHROPIC:
        return ChatAnthropic(model=model.name, max_tokens=8192)
    elif model.provider == LLMProvider.OPENAI:
        return ChatOpenAI(model=model.name, max_tokens=8192)
    elif model.provider == LLMProvider.GOOGLE:
        return ChatGoogleGenerativeAI(model=model.name, max_output_tokens=8192)
    elif model.provider == LLMProvider.AWS:
        return ChatBedrock(
            model_id=model.name,
            model_kwargs={"max_tokens": 8192},
        )
    else:
        raise ValueError(f"Unsupported model provider: {model.provider}")


@asynccontextmanager
async def get_tools(
    mcpServers: list[MCPServerConfig],
    hiveInstances: list[HiveInstance],
    progress_callback: Optional[callable] = None,
):
    if not mcpServers and not hiveInstances:
        yield []
        return

    config = {}

    if mcpServers:
        for mcpServer in mcpServers:
            config[mcpServer.name] = {
                "url": mcpServer.url,
                "transport": mcpServer.transport,
            }

    if hiveInstances:
        for hiveInstance in hiveInstances:
            config[hiveInstance.id] = {
                "url": f"{MCP_SERVER_URL}/{hiveInstance.id}/sse?x-api-key={hiveInstance.apiKey.key}",
                "transport": "sse",
            }

    client = MultiServerMCPClient(config)
    tools = await client.get_tools(progress_callback=progress_callback)
    logger.info(f"Loaded {len(tools)} tools")
    yield tools


class Agent:
    def __init__(
        self,
        name: str,
        prompt: str = None,
        model: Union[str, Model] = "claude-3-5-sonnet-20240620",
        fallback_models: list[Model] | None = None,
        supported_content_types: list[str] = ["text", "text/plain"],
        initial_state: list[BaseMessage] = None,
        context: str = None,
        tools: list = None,
    ):
        self.name = name
        self.prompt = prompt
        self.prompt += f"\nFollowing context is a global space context. It will have a summary about the whole space (all calls that took place, all chat that took place etc.). You should use this to get a general understanding of the ongoing project or conversation. Also if there is no context, it means this is a fresh interaction and there is no previous context.\n{context}"


        # Handle both string and Model object inputs for backward compatibility
        if isinstance(model, str):
            # Default to Anthropic for string inputs
            model_obj = Model(name=model, provider=LLMProvider.ANTHROPIC)
        else:
            model_obj = model

        # Create the primary LLM instance
        primary_llm = _create_llm_instance(model_obj)

        # Prepare fallbacks (if any)
        fallback_llms = []
        if not fallback_models:
            # If caller hasn't provided explicit fallbacks we fall back to a
            # sensible cross-provider default list so that the agent can still
            # respond even when the primary model is unavailable.
            fallback_models = [
                Model(name="gpt-4o-mini", provider=LLMProvider.OPENAI),
                Model(name="gemini-1.5-pro-latest", provider=LLMProvider.GOOGLE),
            ]

        for fb_model in fallback_models or []:
            try:
                fallback_llms.append(_create_llm_instance(fb_model))
            except Exception as e:
                logger.error(
                    f"Failed to instantiate fallback model {fb_model.name} ({fb_model.provider}): {e}"
                )

        # Attach fallbacks using LangChain's built-in helper if we have any
        if fallback_llms:
            try:
                self.model = primary_llm.with_fallbacks(fallback_llms)
            except Exception as e:
                logger.error(f"Failed to attach fallback models: {e}")
                self.model = primary_llm
        else:
            self.model = primary_llm

        self.supported_content_types = supported_content_types
        self.tools = tools if tools is not None else []
        self.graph = None
        self.memory = MemorySaver()
        self.initial_state = initial_state
        self.context = context

    def _prompt(self, prompt: str):
        return f"""
        {prompt}

        Context:
        {self.context}

        Remember: 
        - Your job is to complete the given task.
        - You can ask user for additional information if needed to complete the task. Respond with input_required status and provide a message to the user.
        - If task can not be completed even with additional input from user or if you are not supposed to entertain such requests, respond with error status and provide an error message to the user.
        - If task is completed, respond with completed status and provide a final response to the user. Do not ask any follow up question to continue the chat.
        """

    async def initialize_graph(self, sessionId: str):
        if self.graph:
            return

        self.graph = create_react_agent(
            self.model,
            prompt=self.prompt,
            tools=self.tools,
            checkpointer=self.memory,
        )

        if self.initial_state:
            self.graph.update_state(
                self._get_config(sessionId), {"messages": self.initial_state}
            )

    def _get_config(self, session_id: str):
        return {"configurable": {"thread_id": session_id}}

    async def stream(
        self, message: HumanMessage, session_id: str
    ) -> AsyncIterable[Union[AIMessageChunk, ToolMessageChunk]]:
        await self.initialize_graph(session_id)
        inputs = {"messages": [message]}
        config = self._get_config(session_id)

        logger.info(
            f"Streaming agent with query: {message}, sessionId: {session_id}, current state: {self.graph.get_state(config)}"
        )

        async for chunk, _ in self.graph.astream(
            inputs, config, stream_mode="messages"
        ):
            yield chunk

    def get_current_state(self, session_id: str):
        return self.graph.get_state(self._get_config(session_id))
