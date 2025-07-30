import asyncio

from autogen_agentchat.agents import CodeExecutorAgent
from autogen_agentchat.conditions import MaxMessageTermination
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.ui import Console
from autogen_core.models import ModelFamily
from autogen_ext.code_executors.local import LocalCommandLineCodeExecutor
from autogen_ext.models.openai import OpenAIChatCompletionClient


async def main() -> None:
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
    code_executor = LocalCommandLineCodeExecutor(work_dir='_code_executor_directory', timeout=10)
    agent = CodeExecutorAgent(
        name="code_executor_agent",
        code_executor=code_executor,
        system_message="我是一个代码执行代理，会执行你提供的 Python 代码。",
        model_client=custom_model_client,
    )
    # termination = TextMentionTermination("TERMINATE")
    # termination = TextMentionTermination("exit", sources=["agent"])
    termination = MaxMessageTermination(max_messages=3)
    team = RoundRobinGroupChat([agent], termination_condition=termination)
    await Console(team.run_stream(task="你好，请问直径为4的圆的面积是多少？"))


asyncio.run(main())
