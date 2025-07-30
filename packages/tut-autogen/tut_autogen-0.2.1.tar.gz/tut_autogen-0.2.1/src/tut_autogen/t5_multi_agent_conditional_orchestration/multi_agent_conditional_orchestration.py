import asyncio

from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.conditions import MaxMessageTermination
from autogen_agentchat.teams import DiGraphBuilder, GraphFlow
from autogen_core.models import ModelFamily
from autogen_ext.models.openai import OpenAIChatCompletionClient
from loguru import logger


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

    agent_a = AssistantAgent(
        "A",
        model_client=model_client,
        system_message="Detect if the input is in Chinese. If it is, say 'yes', else say 'no', and nothing else.",
    )
    agent_b = AssistantAgent("B", model_client=model_client, system_message="Translate input to English.")
    agent_c = AssistantAgent("C", model_client=model_client, system_message="Translate input to Chinese.")

    # Create a directed graph with conditional branching flow A -> B ("yes"), A -> C (otherwise).
    builder = DiGraphBuilder()
    builder.add_node(agent_a).add_node(agent_b).add_node(agent_c)
    # Create conditions as callables that check the message content.
    builder.add_edge(agent_a, agent_b, condition=lambda msg: "yes" in msg.to_model_text())
    builder.add_edge(agent_a, agent_c, condition=lambda msg: "yes" not in msg.to_model_text())
    graph = builder.build()

    # Create a GraphFlow team with the directed graph.
    team = GraphFlow(
        participants=[agent_a, agent_b, agent_c],
        graph=graph,
        termination_condition=MaxMessageTermination(5),
    )

    # Run the team and print the events.
    async for event in team.run_stream(task="AutoGen is a framework for building AI agents."):
        print(event)


asyncio.run(main())
