# Runtime Authorization

Runtime authorization is enforcement that happens at the moment of execution — not before the agent starts, and not after the tool runs.

## Why it matters for AI agents

AI agents make tool calls dynamically. The set of calls an agent will make cannot be fully enumerated at deploy time. Prompt instructions, fine-tuning, and output filters all operate on text and model behavior. None of them are enforcement mechanisms in the software security sense.

Runtime authorization answers a different question: **should this specific tool call, with these specific arguments, be executed right now?**

This is the same question that IAM, Open Policy Agent, and API gateways answer for non-AI systems. ShadowAudit brings that model to AI agent tool use.

## Where ShadowAudit enforces

```
Agent → [ShadowAudit Gate] → Tool
```

The gate sits at the boundary between the agent and the tool. It receives the structured arguments the agent is passing to the tool — not a prompt, not a response, but the actual JSON or string payload that would cause the tool to act.

Enforcement happens before `tool.run()` is called. If a call is denied, the tool function is never invoked.

## What ShadowAudit evaluates

The gate receives:

- **`agent_id`**: which agent is making the call
- **`capability`**: the type of action being requested (e.g., `shell.execute`, `payments.transfer`)
- **`payload`**: the tool arguments (command string, amount, file path, etc.)
- **`policy_context`** (optional): runtime metadata like environment, user role, tenant

It evaluates these against a policy and returns one of three decisions: `allow`, `deny`, or `require_approval`.

## Comparison to alternative approaches

| Approach | When it runs | Deterministic? | Covers tool execution? |
|---|---|---|---|
| System prompt instructions | Before the agent starts | No | No |
| Output filters / moderation | After the model generates | No | No |
| ShadowAudit gate | At tool call time | Yes | Yes |

Runtime authorization does not replace prompt design or output monitoring. It is the enforcement layer that makes the others auditable: you can verify that policy was actually applied at the point where consequences occur.

## Related concepts

- [Fail-closed enforcement](fail-closed-enforcement.md)
- [Policy model](policy-model.md)
- [Audit chain](audit-chain.md)
