import asyncio

from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.agents import CodeExecutorAgent
from autogen_agentchat.conditions import MaxMessageTermination
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.ui import Console
from autogen_core.models import ModelFamily
from autogen_ext.code_executors.local import LocalCommandLineCodeExecutor
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_ext.tools.mcp import SseServerParams
from autogen_ext.tools.mcp import mcp_server_tools
from loguru import logger


async def main() -> None:
    logger.debug("Starting main function...")
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

    server_params = SseServerParams(url="http://127.0.0.1:8000/sse")
    tools = await mcp_server_tools(server_params)
    logger.info(f"tools: {len(tools)}")
    agent1 = AssistantAgent(
        name="tool_user",
        model_client=custom_model_client,
        tools=tools,
        system_message="你是一个工具的调用的助手，请你直接给出计算结果。不要解释你的计算过程。",
    )

    code_executor = LocalCommandLineCodeExecutor(work_dir='_code_executor_directory', timeout=10)
    agent2 = CodeExecutorAgent(
        name="code_executor_agent",
        code_executor=code_executor,
        system_message="我是一个代码执行代理，会执行你提供的 Python 代码。执行代码后，直接给出最终的答案。不要解释你的计算过程。最终结果必须以|||开始，以|||结束。例如：|||123|||",
        model_client=custom_model_client,
    )

    termination = MaxMessageTermination(max_messages=3)
    team = RoundRobinGroupChat([agent1, agent2], termination_condition=termination)
    task = "你好，请问直径为4的圆的面积是多少？根据这个数字计算正方体的体积是多少？直接回答给出最终结果。"

    # run 1
    logger.debug(f"{'>' * 10}")
    await Console(team.run_stream(task=task))
    logger.debug(f"{'<' * 10}")

    # run 2
    logger.debug(f"{'>' * 10}")
    messages = []
    stream = team.run_stream(task=task)
    async for message in stream:
        logger.debug(f"message: {message}")
        messages.append(message)
    logger.success(f"final messages: {messages[-1].messages[-1].content}")
    logger.debug(f"{'<' * 10}")


asyncio.run(main())
