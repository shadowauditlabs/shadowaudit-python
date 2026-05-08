# Fintech Agent Demo — ShadowAudit Test Project

A realistic production-style fintech AI agent built with LangChain `BaseTool` subclasses. Designed to test ShadowAudit's static analysis scanner (`shadowaudit check`) against a real-world codebase.

## Architecture

```
src/fintech_agent/
├── tools/                    # Tool definitions (BaseTool subclasses)
│   ├── payment_tools.py      # PaymentTool, RefundTool, WireTransferTool
│   ├── account_tools.py      # DeleteAccountTool, UpdateAccountTool, BulkDataExportTool
│   └── readonly_tools.py     # BalanceInquiryTool, TransactionHistoryTool
└── agents/                   # Agent builders (wrap tools with ShadowAuditTool)
    ├── payment_agent.py      # Wraps PaymentTool, RefundTool (WireTransferTool UNGATED)
    └── admin_agent.py        # Wraps DeleteAccount, UpdateAccount, Balance, History (BulkExport UNGATED)
```

## Tool Inventory

| Tool | Risk Category | Delta | Gated? | File |
|---|---|---|---|---|
| PaymentTool | payment_initiation | 0.3 | ✅ | tools/payment_tools.py |
| RefundTool | payment_initiation | 0.3 | ✅ | tools/payment_tools.py |
| WireTransferTool | payment_initiation | 0.3 | ❌ | tools/payment_tools.py |
| DeleteAccountTool | delete | 0.2 | ✅ | tools/account_tools.py |
| UpdateAccountTool | update | 0.3 | ✅ | tools/account_tools.py |
| BulkDataExportTool | data_export | 0.15 | ❌ | tools/account_tools.py |
| BalanceInquiryTool | read_only | 1.0 | ✅ | tools/readonly_tools.py |
| TransactionHistoryTool | read_only | 1.0 | ✅ | tools/readonly_tools.py |

**Key design decision**: Tools are defined in `tools/` and wrapped in `agents/` — this tests ShadowAudit's cross-file wrapper detection.

## Testing ShadowAudit

```bash
# Install
pip install shadowaudit

# Scan the project
shadowaudit check src/

# Expected output:
#   [SCAN] 8 tool(s) found
#   Gated: 6, Ungated: 2, High-risk ungated: 2

# CI mode — fails if high-risk tools are ungated
shadowaudit check src/ --fail-on-ungated
# Exit code: 1 (fails because WireTransferTool and BulkDataExportTool are ungated)

# Generate HTML assessment report
shadowaudit assess src/ --taxonomy financial

# Run the verification tests
pip install -e ".[dev]"
pytest tests/ -v
```

## What This Demonstrates

1. **Cross-file detection** — tools in `tools/*.py`, wrappers in `agents/*.py`
2. **Intentional gaps** — 2 tools left ungated to simulate real oversights
3. **CI integration** — `--fail-on-ungated` blocks deployment
4. **Risk categorization** — automatic delta assignment from tool names
5. **Framework detection** — LangChain BaseTool identified from imports
