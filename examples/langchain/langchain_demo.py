"""Minimal LangChain Integration Demo."""

from shadowaudit.framework.langchain import ShadowAuditTool
from shadowaudit.errors import AgentActionBlocked
from langchain.tools import tool

@tool
def shell_tool(command: str) -> str:
    """Execute a shell command."""
    return "Executed"

safe_shell = ShadowAuditTool(
    tool=shell_tool,
    agent_id="langchain-agent",
    risk_category="execute"
)

print("Attempting to run a safe command...")
print(safe_shell.run({"command": "echo 'hello world'"}))

print("\nAttempting to run a dangerous command...")
try:
    safe_shell.run({"command": "exec rm -rf /"})
except AgentActionBlocked as e:
    print(f"BLOCKED: {e}")
