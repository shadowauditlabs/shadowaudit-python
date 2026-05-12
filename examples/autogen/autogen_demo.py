"""Minimal AutoGen Integration Demo."""
from shadowaudit.framework.autogpt import AutoGPTAdapter
from shadowaudit.core.gate import Gate

gate = Gate()
adapter = AutoGPTAdapter(gate)

def mock_shell_tool(command: str) -> str:
    """Mock AutoGen tool."""
    return "Executed"

# In a real AutoGen setup, you would use wrap_tool
# For this demo, we simulate direct gating:
print("Attempting to run a dangerous command...")
result = gate.evaluate(
    agent_id="autogen-agent",
    task_context="shell",
    risk_category="execute",
    payload={"command": "exec rm -rf /"}
)

if not result.passed:
    print(f"BLOCKED: {result.reason}")
