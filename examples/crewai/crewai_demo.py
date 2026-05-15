"""Minimal CrewAI Integration Demo."""
from capfence.framework.crewai import CapFenceCrewAITool
from capfence.errors import AgentActionBlocked

class MockCrewAITool:
    name = "shell"
    description = "Execute a shell command"
    
    def run(self, command: str) -> str:
        return "Executed"

safe_shell = CapFenceCrewAITool(
    tool=MockCrewAITool(),
    agent_id="crewai-agent",
    risk_category="execute"
)

print("Attempting to run a dangerous command...")
try:
    safe_shell.run("exec rm -rf /")
except AgentActionBlocked as e:
    print(f"BLOCKED: {e.detail}")
