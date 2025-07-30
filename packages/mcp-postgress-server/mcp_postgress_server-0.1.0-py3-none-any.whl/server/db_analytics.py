from mcp.server.fastmcp import FastMCP
from server.db_analytics_core import EmployeeAnalyticsMCP

mcp = FastMCP()
analytics = EmployeeAnalyticsMCP()

@mcp.tool(
    name="analyse_db",
    description="Ask a natural language question about your data or the web. The system will use both your database and web search to answer."
)
async def analyse_db(question: str):
    return await analytics.answer_question(question)

if __name__ == "__main__":
    mcp.run()
