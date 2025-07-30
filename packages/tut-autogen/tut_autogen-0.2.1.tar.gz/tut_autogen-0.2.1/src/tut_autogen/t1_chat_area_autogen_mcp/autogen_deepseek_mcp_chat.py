import asyncio

from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.conditions import TextMentionTermination
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.ui import Console
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_ext.tools.mcp import SseServerParams
from autogen_ext.tools.mcp import mcp_server_tools
from autogen_core.models import ModelFamily


async def main() -> None:
    server_params = SseServerParams(url="http://127.0.0.1:8000/sse")
    tools = await mcp_server_tools(server_params)
    print(tools)
    custom_model_client = OpenAIChatCompletionClient(
        model="deepseek-chat",
        api_key="sk-bf45e97095c64d8aa0336a7857563493",
        base_url="https://api.deepseek.com",
        model_info={
            "vision": False,
            "function_calling": True,
            "json_output": True,
            "family": ModelFamily.ANY,
            "structured_output": True,
        },
    )

    agent = AssistantAgent(name="tool_user", model_client=custom_model_client, tools=tools)
    termination = TextMentionTermination("TERMINATE")
    team = RoundRobinGroupChat([agent], termination_condition=termination)
    await Console(team.run_stream(task="你好，请问直径为4的圆的面积是多少？"))


asyncio.run(main())
