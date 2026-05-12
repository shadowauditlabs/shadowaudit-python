"""MCP gateway server — intercepts MCP tool calls through ShadowAudit Gate.

Acts as a transparent proxy between an MCP client and MCP server.
Every tool/call request is evaluated by the Gate before forwarding.

Usage:
    from shadowaudit.mcp.gateway import MCPGatewayServer
    from shadowaudit.core.gate import Gate

    gateway = MCPGatewayServer(
        upstream_command=["python", "-m", "mcp_server_filesystem", "/tmp"],
        gate=Gate(),
        agent_id="mcp-agent-1",
    )
    gateway.run()  # blocks, proxies stdio
"""

from __future__ import annotations

import json
import logging
import subprocess
import sys
import threading
from typing import Any, cast

from shadowaudit.core.gate import Gate
from shadowaudit.core.fsm import FailClosedFSM
from shadowaudit.types import GateResult
from shadowaudit.errors import GatewayError

logger = logging.getLogger(__name__)

MAX_MESSAGE_SIZE = 10 * 1024 * 1024  # 10 MB


class MCPGatewayServer:
    """Transparent stdio proxy for MCP with ShadowAudit gating.

    Intercepts JSON-RPC messages for tool calls and runs the payload
    through Gate.evaluate() before forwarding to the upstream server.
    """

    def __init__(
        self,
        upstream_command: list[str],
        gate: Gate | None = None,
        agent_id: str = "mcp-gateway",
        default_risk_category: str | None = None,
    ) -> None:
        self._upstream_command = upstream_command
        self._gate = gate or Gate()
        self._agent_id = agent_id
        self._default_risk_category = default_risk_category
        self._fsm = FailClosedFSM()
        self._proc: subprocess.Popen[str] | None = None
        self._lock = threading.Lock()

    def _start_upstream(self) -> subprocess.Popen[str]:
        """Launch the upstream MCP server process."""
        logger.info("Starting upstream MCP server: %s", " ".join(self._upstream_command))
        return subprocess.Popen(
            self._upstream_command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )

    def _read_message(self, stream: Any) -> dict[str, Any] | None:
        """Read a single JSON-RPC message from stream (Content-Length protocol)."""
        headers: dict[str, str] = {}
        while True:
            line = stream.readline()
            if not line:
                return None
            line = line.strip()
            if not line:
                break
            if ":" in line:
                key, value = line.split(":", 1)
                headers[key.strip().lower()] = value.strip()

        try:
            length = int(headers.get("content-length", 0))
        except ValueError:
            logger.warning("Invalid Content-Length header")
            return None
        if length <= 0 or length > MAX_MESSAGE_SIZE:
            logger.warning("Content-Length out of bounds: %d", length)
            return None

        body = stream.read(length)
        try:
            return cast(dict[str, Any], json.loads(body))
        except json.JSONDecodeError:
            logger.warning("Invalid JSON from upstream: %s", body[:200])
            return None

    def _write_message(self, stream: Any, message: dict[str, Any]) -> None:
        """Write a JSON-RPC message to stream."""
        body = json.dumps(message, separators=(",", ":"), ensure_ascii=False)
        header = f"Content-Length: {len(body.encode('utf-8'))}\r\n\r\n"
        stream.write(header + body)
        stream.flush()

    def _is_tool_call(self, message: dict[str, Any]) -> bool:
        """Check if message is a tools/call request."""
        method = message.get("method", "")
        return method in ("tools/call", "tool/call", "call_tool")

    def _extract_tool_payload(self, message: dict[str, Any]) -> dict[str, Any]:
        """Extract tool name and arguments from a tools/call request."""
        params = message.get("params", {})
        return {
            "tool_name": params.get("name", "unknown"),
            "arguments": params.get("arguments", {}),
        }

    def _build_blocked_response(self, request: dict[str, Any], result: GateResult) -> dict[str, Any]:
        """Build a JSON-RPC error response for a blocked tool call."""
        return {
            "jsonrpc": "2.0",
            "id": request.get("id"),
            "error": {
                "code": -32000,
                "message": "ShadowAudit blocked this tool call",
                "data": {
                    "reason": result.reason,
                    "risk_score": result.risk_score,
                    "threshold": result.threshold,
                    "risk_category": result.risk_category,
                },
            },
        }

    def _forward_and_respond(self, request: dict[str, Any]) -> dict[str, Any] | None:
        """Forward request to upstream, return response."""
        with self._lock:
            if self._proc is None or self._proc.stdin is None or self._proc.stdout is None:
                logger.error("Upstream process not available")
                return None

            self._write_message(self._proc.stdin, request)
            return self._read_message(self._proc.stdout)

    def _handle_message(self, message: dict[str, Any]) -> dict[str, Any] | None:
        """Process a single JSON-RPC message."""
        if not self._is_tool_call(message):
            # Non-tool call: forward transparently
            return self._forward_and_respond(message)

        # Tool call: evaluate through Gate
        payload = self._extract_tool_payload(message)
        tool_name = payload["tool_name"]
        arguments = payload["arguments"]

        # Determine risk category from tool name heuristics
        risk_category = self._default_risk_category
        if risk_category is None:
            risk_category = self._guess_category(tool_name)

        result = self._gate.evaluate(
            agent_id=self._agent_id,
            task_context=tool_name,
            risk_category=risk_category,
            payload=arguments,
        )

        outcome = self._fsm.transition(result)
        if outcome.decision != "pass":
            logger.warning(
                "Blocked MCP tool call: %s (score=%.2f, threshold=%.2f)",
                tool_name, result.risk_score or 0.0, result.threshold or 0.0,
            )
            return self._build_blocked_response(message, result)

        # Allowed: forward to upstream
        return self._forward_and_respond(message)

    @staticmethod
    def _guess_category(tool_name: str) -> str | None:
        """Heuristic risk category from tool name."""
        name = tool_name.lower()
        if any(k in name for k in ("shell", "exec", "run", "command", "bash", "sh")):
            return "command_execution"
        if any(k in name for k in ("pay", "transfer", "send", "disburse", "stripe")):
            return "payment_initiation"
        if any(k in name for k in ("delete", "remove", "drop", "wipe")):
            return "delete"
        if any(k in name for k in ("write", "update", "modify", "patch")):
            return "write"
        if any(k in name for k in ("read", "get", "list", "view", "query")):
            return "read_only"
        return None

    def run(self) -> None:
        """Start the gateway and block on stdio proxying."""
        self._proc = self._start_upstream()
        if self._proc.stdout is None:
            raise GatewayError("Failed to start upstream process")

        # Thread to forward upstream stderr to our stderr for debugging
        def _drain_stderr() -> None:
            with self._lock:
                proc = self._proc
            if proc is None or proc.stderr is None:
                return
            for line in proc.stderr:
                logger.debug("[upstream stderr] %s", line.rstrip())

        stderr_thread = threading.Thread(target=_drain_stderr, daemon=True)
        stderr_thread.start()

        try:
            while True:
                message = self._read_message(sys.stdin)
                if message is None:
                    break

                response = self._handle_message(message)
                if response is not None:
                    self._write_message(sys.stdout, response)
        except KeyboardInterrupt:
            logger.info("Gateway shutting down (KeyboardInterrupt)")
        except (BrokenPipeError, OSError) as e:
            logger.info("Gateway shutting down (%s)", type(e).__name__)
        finally:
            with self._lock:
                if self._proc is not None:
                    self._proc.terminate()
                    try:
                        self._proc.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        self._proc.kill()
