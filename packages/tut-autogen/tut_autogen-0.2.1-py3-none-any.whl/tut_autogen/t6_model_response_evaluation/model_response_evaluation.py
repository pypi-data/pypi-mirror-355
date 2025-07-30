import asyncio
import json

import pandas as pd
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.base._task import TaskResult
from autogen_agentchat.conditions import TextMessageTermination
from autogen_agentchat.messages import TextMessage
from autogen_agentchat.teams import DiGraphBuilder, GraphFlow
from autogen_core.models import ModelFamily
from autogen_ext.models.openai import OpenAIChatCompletionClient
from loguru import logger

from prompts import *


async def main() -> None:
    logger.debug("Starting main function...")
    model_client = OpenAIChatCompletionClient(
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

    agent_a = AssistantAgent("A", model_client=model_client, system_message=system_message_a)
    agent_b = AssistantAgent("B", model_client=model_client, system_message=system_message_b)
    agent_c = AssistantAgent("C", model_client=model_client, system_message=system_message_c)

    builder = DiGraphBuilder()
    builder.add_node(agent_a).add_node(agent_b).add_node(agent_c)
    builder.add_edge(agent_a, agent_b).add_edge(agent_b, agent_c)
    graph = builder.build()

    team = GraphFlow(
        participants=[agent_a, agent_b, agent_c],
        graph=graph,
        termination_condition=TextMessageTermination("总结结束"),
    )

    df = pd.read_csv("model_response_evaluation.csv")
    results = []
    for idx, row in df.iterrows():
        q, r, gt = row
        task = user_prompt.substitute(query=q, response=r, ground_truth=gt)
        async for event in team.run_stream(task=task):
            if isinstance(event, TextMessage):
                logger.debug(f"message received: {event}")
            if isinstance(event, TaskResult):
                logger.info(f"Task completed: {event}")
                for message in event.messages:
                    if message.source == "C":
                        target_message = json.loads(message.content)
                        result = target_message['conclusion']
                        result['query'] = q
                        result['response'] = r
                        result['ground_truth'] = gt
                        results.append(result)
                        logger.success(f"message received: {result}")
        if idx == 1:
            break
    pd.DataFrame(results).to_csv("model_response_evaluation_result.csv", index=False)


if __name__ == '__main__':
    asyncio.run(main())
