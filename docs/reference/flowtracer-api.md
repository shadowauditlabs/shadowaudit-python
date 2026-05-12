# FlowTracer API Reference

`FlowTracer` tracks data movement between agents and propagates trust levels through multi-agent workflows.

```python
from shadowaudit import FlowTracer, TrustLevel

tracer = FlowTracer()
```

## Trust levels

Lower trust values dominate higher trust values during propagation.

| Level | Meaning |
|---|---|
| `TrustLevel.SYSTEM` | Internal system agent under operator control. |
| `TrustLevel.INTERNAL` | Internal agent with limited scope. |
| `TrustLevel.EXTERNAL` | Agent that processed external data. |
| `TrustLevel.UNTRUSTED` | Agent that processed user-supplied or third-party content. |

## Record output

```python
tracer.record_output(
    source_agent="web-scraper",
    data={"url": "https://example.com", "content": page_html},
    trust=TrustLevel.UNTRUSTED,
)
```

## Record a flow

```python
tracer.record_flow(
    source_agent="web-scraper",
    destination_agent="payment-agent",
    data={"amount": 5000, "account": "external"},
)
```

## Annotate a receiving agent

```python
annotation = tracer.annotate(
    receiving_agent="payment-agent",
    source_agents=["web-scraper"],
    declared_trust=TrustLevel.SYSTEM,
)

print(annotation.effective_trust)   # TrustLevel.UNTRUSTED
print(annotation.contaminated_by)   # ["web-scraper"]
```

## Inspect trust

```python
trust = tracer.get_agent_trust("payment-agent")
summary = tracer.flow_summary()
```

## Reset

```python
tracer.reset()
```

## Related concepts

- [Trust propagation](../concepts/trust-propagation.md)
- [Runtime authorization](../concepts/runtime-authorization.md)
