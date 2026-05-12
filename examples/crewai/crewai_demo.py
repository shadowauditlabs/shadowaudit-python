"""Minimal CrewAI Integration Demo."""
from shadowaudit.framework.crewai import ShadowAuditCrewAITool
from shadowaudit.errors import AgentActionBlocked

class MockCrewAITool:
    name = "shell"
    description = "Execute a shell command"
    
    def run(self, command: str) -> str:
        return "Executed"

safe_shell = ShadowAuditCrewAITool(
    tool=MockCrewAITool(),
    agent_id="crewai-agent",
    risk_category="execute"
)

print("Attempting to run a dangerous command...")
try:
    safe_shell.run("exec rm -rf /")
except AgentActionBlocked as e:
    print(f"BLOCKED: {e.detail}")
