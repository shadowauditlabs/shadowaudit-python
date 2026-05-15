# Fintech Agent Example

A complete example of a financial agent gated with CapFence: the agent can read account data freely, requires approval for transfers over $1,000, and is hard-blocked from transfers over $50,000.

## Policy

```yaml
# policies/fintech_agent.yaml

deny:
  - capability: payments.transfer
    amount_gt: 50000
  - capability: payments.transfer
    environment: production
    user_role: unverified

require_approval:
  - capability: payments.transfer
    amount_gt: 1000
  - capability: payments.refund
    amount_gt: 500
  - capability: account.close

allow:
  - capability: account.read
  - capability: transaction.read
  - capability: payments.transfer
    amount_lte: 1000
  - capability: payments.refund
    amount_lte: 500

approval_timeout_seconds: 1800
```

## Tools

```python
from capfence import CapFenceTool

class AccountReadTool:
    name = "account_read"
    def run(self, account_id: str) -> dict:
        return db.get_account(account_id)

class TransferTool:
    name = "transfer"
    def run(self, from_account: str, to_account: str, amount: float) -> dict:
        return payments_api.transfer(from_account, to_account, amount)

safe_read = CapFenceTool(
    tool=AccountReadTool(),
    agent_id="fintech-agent",
    capability="account.read",
    policy_path="policies/fintech_agent.yaml"
)

safe_transfer = CapFenceTool(
    tool=TransferTool(),
    agent_id="fintech-agent",
    capability="payments.transfer",
    policy_path="policies/fintech_agent.yaml"
)
```

## Agent

```python
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate

llm = ChatOpenAI(model="gpt-4o")
tools = [safe_read, safe_transfer]

prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a financial assistant. Help users manage their accounts."),
    ("human", "{input}"),
    ("placeholder", "{agent_scratchpad}")
])

agent = create_openai_tools_agent(llm, tools, prompt)
executor = AgentExecutor(agent=agent, tools=tools, verbose=True)
```

## Invocation

```python
# Small transfer — allowed immediately
executor.invoke({
    "input": "Transfer $500 from account A to account B"
})

# Large transfer — paused for approval
executor.invoke({
    "input": "Transfer $5,000 from account A to account B"
})
# Agent receives: "Action pending approval (request_id: a1b2c3d4)"

# Very large transfer — hard blocked
executor.invoke({
    "input": "Transfer $100,000 from account A to account B"
})
# Agent receives: AgentActionBlocked: payments.transfer denied (amount_gt=50000)
```

## Approve the pending transfer

```bash
capfence pending-approvals
capfence approve a1b2c3d4
```

## Audit log

```bash
capfence logs --audit-log audit.db --json
```
