from mcp.server.fastmcp import FastMCP
from agentmail_toolkit.mcp import AgentMailToolkit

mcp = FastMCP(name="AgentMail", tools=AgentMailToolkit().get_tools())

if __name__ == "__main__":
    mcp.run(transport="stdio")
