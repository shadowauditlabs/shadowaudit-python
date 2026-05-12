# Trust Propagation

In multi-agent systems, one agent's output often becomes another agent's tool input. Trust propagation tracks that data movement so high-privilege actions can account for where their inputs came from.

## The problem

An agent may appear trusted at the moment it calls a tool, but its payload may have originated from untrusted input:

```text
Web scraper → Parser → Payment agent → payments.transfer
```

If the payment payload was derived from scraped or user-controlled content, the final authorization decision should know that.

## FlowTracer

ShadowAudit provides `FlowTracer` for recording cross-agent data movement.

```python
from shadowaudit import FlowTracer, TrustLevel

tracer = FlowTracer()

tracer.record_output(
    source_agent="web-scraper",
    data={"content": page_html},
    trust=TrustLevel.UNTRUSTED,
)

tracer.record_flow(
    source_agent="web-scraper",
    destination_agent="payment-agent",
    data={"amount": 5000},
)

annotation = tracer.annotate(
    receiving_agent="payment-agent",
    source_agents=["web-scraper"],
    declared_trust=TrustLevel.SYSTEM,
)

print(annotation.effective_trust)  # TrustLevel.UNTRUSTED
```

## Trust levels

| Trust level | Use case |
|---|---|
| `SYSTEM` | Internal system-controlled agent. |
| `INTERNAL` | Internal agent with limited scope. |
| `EXTERNAL` | Agent that processed external APIs, files, or web content. |
| `UNTRUSTED` | Agent that processed user-supplied or third-party content. |

Lower trust propagates forward. If an untrusted source contributes to a payload, the resulting annotation remains untrusted even when the receiving agent is normally trusted.

## Related concepts

- [Runtime authorization](runtime-authorization.md)
- [FlowTracer API](../reference/flowtracer-api.md)
- [MCP governance](../integrations/mcp.md)
