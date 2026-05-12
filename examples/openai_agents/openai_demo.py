"""Minimal OpenAI Agents Integration Demo."""
import asyncio
import json
from shadowaudit.framework.openai_agents import ShadowAuditOpenAITool, AgentActionBlocked

class MockOpenAITool:
    name = "shell"
    description = "Execute a shell command"
    
    async def on_invoke_tool(self, context, input_json: str) -> str:
        return "Executed"

async def main():
    safe_shell = ShadowAuditOpenAITool(
        tool=MockOpenAITool(),
        agent_id="openai-agent",
        risk_category="execute"
    )

    print("Attempting to run a dangerous command...")
    try:
        await safe_shell.on_invoke_tool(None, json.dumps({"command": "exec rm -rf /"}))
    except AgentActionBlocked as e:
        print(f"BLOCKED: {e.detail}")

if __name__ == "__main__":
    asyncio.run(main())
