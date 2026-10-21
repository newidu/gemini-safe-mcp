"""Safe MCP server for Gemini Custom Apps.

Exposes only workspace-scoped file operations and a small command allowlist.
Do not expose this service to the public internet without HTTPS and authentication.
"""
from __future__ import annotations

import os
import secrets
import shlex
import subprocess
from pathlib import Path

from mcp.server.fastmcp import FastMCP
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
import uvicorn

WORKSPACE = Path(os.environ.get("MCP_WORKSPACE", "/home/ubuntu/gemini-workspace")).resolve()
UNSAFE_LOCAL = os.environ.get("MCP_UNSAFE_LOCAL", "0") == "1"
# Unsafe mode is deliberately forced to loopback and can never be exposed by setting MCP_HOST.
MCP_HOST = "127.0.0.1" if UNSAFE_LOCAL else os.environ.get("MCP_HOST", "127.0.0.1")
MCP_PORT = int(os.environ.get("MCP_PORT", "8000"))
MCP_AUTH_TOKEN = os.environ.get("MCP_AUTH_TOKEN", "")
MAX_READ_BYTES = 200_000
MAX_WRITE_BYTES = 200_000
ALLOWED_COMMANDS = {"pwd", "ls", "find", "git", "python3", "node", "npm", "pnpm"}

WORKSPACE.mkdir(parents=True, exist_ok=True)
mcp = FastMCP("safe-workspace-control", host=MCP_HOST, port=MCP_PORT)


class BearerAuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        if not MCP_AUTH_TOKEN:
            return JSONResponse({"error": "MCP_AUTH_TOKEN is not configured"}, status_code=503)
        expected = f"Bearer {MCP_AUTH_TOKEN}"
        if not secrets.compare_digest(request.headers.get("authorization", ""), expected):
            return JSONResponse({"error": "Unauthorized"}, status_code=401, headers={"WWW-Authenticate": "Bearer"})
        return await call_next(request)


def safe_path(relative_path: str) -> Path:
    candidate = (WORKSPACE / relative_path).resolve()
    if candidate != WORKSPACE and WORKSPACE not in candidate.parents:
        raise ValueError("Path must stay inside MCP_WORKSPACE")
    return candidate


@mcp.tool()
def list_files(path: str = ".") -> str:
    """List files and directories inside the configured workspace."""
    target = safe_path(path)
    if not target.exists():
        raise ValueError("Path does not exist")
    if target.is_file():
        return str(target.relative_to(WORKSPACE))
    entries = sorted(p.relative_to(WORKSPACE) for p in target.iterdir())
    return "\n".join(str(p) for p in entries) or "(empty)"


@mcp.tool()
def read_file(path: str) -> str:
    """Read a UTF-8 text file inside the configured workspace."""
    target = safe_path(path)
    if not target.is_file():
        raise ValueError("Not a file")
    if target.stat().st_size > MAX_READ_BYTES:
        raise ValueError(f"File is larger than {MAX_READ_BYTES} bytes")
    return target.read_text(encoding="utf-8")


@mcp.tool()
def write_file(path: str, content: str) -> str:
    """Write a UTF-8 text file inside the configured workspace."""
    if len(content.encode("utf-8")) > MAX_WRITE_BYTES:
        raise ValueError(f"Content is larger than {MAX_WRITE_BYTES} bytes")
    target = safe_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    return f"Wrote {target.relative_to(WORKSPACE)}"


@mcp.tool()
def run_command(command: str, timeout_seconds: int = 20) -> str:
    """Run one allowlisted command in the workspace; no shell pipelines or redirects."""
    parts = shlex.split(command)
    if not parts or parts[0] not in ALLOWED_COMMANDS:
        raise ValueError(f"Command not allowed. Allowed programs: {sorted(ALLOWED_COMMANDS)}")
    if any(token in command for token in [";", "&&", "||", "|", ">", "<", "`", "$ ("]):
        raise ValueError("Shell operators, redirects, and command substitution are disabled")
    timeout_seconds = max(1, min(int(timeout_seconds), 60))
    result = subprocess.run(
        parts,
        cwd=WORKSPACE,
        text=True,
        capture_output=True,
        timeout=timeout_seconds,
        check=False,
        env={**os.environ, "HOME": str(WORKSPACE)},
    )
    output = (result.stdout + result.stderr).strip()
    return f"exit={result.returncode}\n{output}"[:20_000]


if UNSAFE_LOCAL:
    @mcp.tool()
    def run_any_shell_command(command: str, timeout_seconds: int = 30) -> str:
        """Run any shell command locally. Enabled only with MCP_UNSAFE_LOCAL=1; never public."""
        timeout_seconds = max(1, min(int(timeout_seconds), 120))
        result = subprocess.run(
            command,
            cwd=WORKSPACE,
            shell=True,
            text=True,
            capture_output=True,
            timeout=timeout_seconds,
            check=False,
            env=os.environ.copy(),
        )
        output = (result.stdout + result.stderr).strip()
        return f"exit={result.returncode}\n{output}"[:20_000]


if __name__ == "__main__":
    # Public deployments require MCP_AUTH_TOKEN. Local-only unsafe mode intentionally
    # remains on the normal FastMCP runner for local development.
    if MCP_UNSAFE_LOCAL:
        mcp.run(transport="streamable-http")
    else:
        app = mcp.streamable_http_app()
        app.add_middleware(BearerAuthMiddleware)
        uvicorn.run(app, host=MCP_HOST, port=MCP_PORT)
