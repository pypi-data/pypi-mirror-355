from nexira_ai_package.vector_db.memory_handler import MemoryHandler as KnowledgeBase
from nexira_ai_package.chat_history.memory_handler import MemoryHandler as ChatHistory
from langgraph.prebuilt import create_react_agent   
from langchain_openai import ChatOpenAI
from nexira_ai_package.app_config import app_config
import os

class ReactAgent():
    def __init__(self, name: str, knowledge_base: KnowledgeBase, chat_history: ChatHistory):
        self.knowledge_base = knowledge_base
        self.chat_history = chat_history
        self.name = name
        self.all_agents = {
            "mini_mavia_agent": 0,
            "block_clans_agent": 1,
            "standard_agent": 2
        }
        self.agent = self.create_llm_agent()
        max_iterations = 3
        recursion_limit = 1 * max_iterations + 1
        self.recursion = {"recursion_limit": recursion_limit}

    # Agent type 0: Mini Mavia
    # Agent type 1: Block Clans
    # Agent type 2: Standard
    def create_llm_agent(self):
        agent_type = self.all_agents[self.name]
        all_tools = self.knowledge_base.get_search_tool()
        if agent_type < len(all_tools):
            tools = [all_tools[agent_type]]
        else:
            tools = all_tools

        tool_names = "and".join([tool.name for tool in tools])
        system_prompt =f"""
        You are a helpful assistant who answers questions using relevant document content retrieved via tools.
        Use the {tool_names} to retrieve document chunks related to the query.
        Base your answer on the retrieved content, citing specific details where relevant.
        In cases of images, please return the image path as it is given in the tool without any modification.
        Please ensure that you return the answer in the same language as the question from the user.
        """

        os.environ["OPENAI_API_KEY"] = app_config.OPENAI_API_KEY or "none"
        llm_model = ChatOpenAI(model="gpt-4o-mini", temperature=0)
        agent = create_react_agent(
            llm_model,
            tools=tools,
            prompt=system_prompt
        )
        return agent

    def get_agent(self):
        return self.agent

    async def print_stream(self, inputs: dict) -> str:
        message = None
        async for s in self.agent.astream(inputs, stream_mode="values"):
            message = s["messages"][-1]
        return message.content if message else ""

    async def process_question(self, query: str, user_id: int, chat_id: int) -> str:
        chat_history = self.chat_history.retrieve_conversation(user_id, chat_id)
        message_history = []
        for history in chat_history:
            message_history.extend(history["messages"])

        message_history = [{"role": msg["role"], "content": msg["content"]} for msg in message_history if not msg["content"].startswith("/")]
        message_history = message_history[-6:]
        message_history.append({"role": "user", "content": query})
        answer = await self.print_stream({"messages": message_history})
        return answer

