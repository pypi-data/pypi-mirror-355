import os
import asyncio
from typing import Any, Dict
from dotenv import load_dotenv

from langchain_community.llms import OpenAI
from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits.sql.base import create_sql_agent
from langchain.tools import Tool
from langchain.agents import initialize_agent, AgentType

import httpx

load_dotenv()

class EmployeeAnalyticsMCP:
    def __init__(self):
        self.db_uri = (
            f"postgresql+psycopg2://{os.getenv('POSTGRES_USER')}:"
            f"{os.getenv('POSTGRES_PASSWORD')}@{os.getenv('POSTGRES_HOST')}:"
            f"{os.getenv('POSTGRES_PORT')}/{os.getenv('POSTGRES_DB')}"
        )
        self.serper_api_key = os.getenv("SERPER_API_KEY")
        self.serper_url = "https://google.serper.dev/search"
        self.llm = OpenAI(temperature=0, openai_api_key=os.getenv("OPENAI_API_KEY"))
        self.db = SQLDatabase.from_uri(self.db_uri)
        self.agent = create_sql_agent(
            llm=self.llm,
            db=self.db,
            verbose=True
        )

    async def search_web(self, query: str) -> str:
        headers = {
            'X-API-KEY': self.serper_api_key,
            'Content-Type': 'application/json'
        }
        payload = {'q': query, 'gl': 'us', 'hl': 'en'}
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.serper_url,
                headers=headers,
                json=payload,
                timeout=30.0
            )
            data = response.json()
            # Return a summary string for the agent
            if "organic" in data and data["organic"]:
                return "\n".join([item.get("title", "") + ": " + item.get("link", "") for item in data["organic"][:3]])
            return str(data)

    def _initialize_agent(self):
        # Synchronous wrapper for async web search
        def sync_search_web(query: str):
            return asyncio.run(self.search_web(query))

        web_search_tool = Tool(
            name="Web Search",
            func=sync_search_web,
            description="Useful for answering questions by searching the web for up-to-date information."
        )

        def run_sql_query(query: str):
            return self.agent.run(query)

        sql_tool = Tool(
            name="Database",
            func=run_sql_query,
            description="Useful for answering questions about data stored in the user's database."
        )

        tools = [web_search_tool, sql_tool]

        agent = initialize_agent(
            tools,
            self.llm,
            agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
            verbose=True
        )
        return agent

    async def answer_question(self, question: str) -> Any:
        # Run the agent in a thread to avoid blocking the event loop
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.agent.run, question)