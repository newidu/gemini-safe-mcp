"""Safe MCP server for Gemini Custom Apps (Modified for unlimited commands & no Auth).

Exposes workspace-scoped file operations and allows running any shell commands locally.
"""
from __future__ import annotations

import os
import shlex
import subprocess
from pathlib import Path

from mcp.server.fastmcp import FastMCP

WORKSPACE = Path(os.environ.get("MCP_WORKSPACE", "/home/ubuntu/gemini-workspace")).resolve()
MCP_HOST = os.environ.get("MCP_HOST", "127.0.0.1")
MCP_PORT = int(os.environ.get("MCP_PORT", "8080"))
MAX_READ_BYTES = 200_000
MAX_WRITE_BYTES = 200_000

WORKSPACE.mkdir(parents=True, exist_ok=True)
mcp = FastMCP("workspace-control", host=MCP_HOST, port=MCP_PORT)


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
def run_any_shell_command(command: str, timeout_seconds: int = 30) -> str:
    """Run any shell command locally inside the workspace with no limits."""
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
    mcp.run(transport="streamable-http")
