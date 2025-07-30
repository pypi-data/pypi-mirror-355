"""
MCP server wrapper for *lumerpy*
--------------------------------

This version relies on the official **mcp‑python‑sdk** so the MCP
initialisation / handshake, framing and error‑wrapping are all handled
for you.  It automatically exposes every public (non‑underscore) callable
inside the **lumerpy** package as an MCP *tool* that Trae (or any other
MCP‑aware IDE) can discover and invoke.

How to run (local tests)
------------------------
$ python mcp_server.py            # or   uv python mcp_server.py

Trae workspace config example
-----------------------------
{
  "mcpServers": {
    "lumerpy": {
      "command": "python",
      "args": ["mcp_server.py"]
    }
  }
}
"""
from __future__ import annotations

import asyncio
import inspect
import json
import logging
from typing import Any, Dict, List

import lumerpy  # your business library
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

logger = logging.getLogger("lumerpy_mcp_server")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

app = Server("lumerpy")  # 1⃣  create the MCP server instance


# ---------------------------------------------------------------------------
# Helper: map Python annotations → minimal JSON‑Schema types
# ---------------------------------------------------------------------------

def _annotation_to_schema(ann: Any) -> Dict[str, Any]:
    """Very small mapper – defaults to string if unknown."""
    mapping = {
        int: {"type": "integer"},
        float: {"type": "number"},
        bool: {"type": "boolean"},
        str: {"type": "string"},
        list: {"type": "array"},
        dict: {"type": "object"},
    }
    # Support typing module hints like list[int]
    if hasattr(ann, "__origin__"):
        origin = ann.__origin__  # noqa: SLF001
        if origin in (list, List):
            return {"type": "array"}
        if origin in (dict, Dict):
            return {"type": "object"}
    return mapping.get(ann, {"type": "string"})


# ---------------------------------------------------------------------------
# list_tools – expose every public callable in lumerpy
# ---------------------------------------------------------------------------


@app.list_tools()
async def list_tools() -> List[Tool]:
    tools: List[Tool] = []

    for name, fn in inspect.getmembers(lumerpy, inspect.isfunction):
        if name.startswith("_"):
            continue  # skip private helpers

        sig = inspect.signature(fn)
        properties = {}
        required: List[str] = []

        for param in sig.parameters.values():
            if param.kind in (param.VAR_POSITIONAL, param.VAR_KEYWORD):
                # *args / **kwargs are not supported over MCP; skip
                continue

            schema = _annotation_to_schema(param.annotation)
            if param.default is inspect.Parameter.empty:
                required.append(param.name)
            properties[param.name] = schema

        tools.append(
            Tool(
                name=name,
                description=fn.__doc__ or f"lumerpy.{name}",
                inputSchema={
                    "type": "object",
                    "properties": properties,
                    "required": required,
                },
            )
        )

    logger.info("Exposed %d lumerpy functions as tools", len(tools))
    return tools


# ---------------------------------------------------------------------------
# call_tool – invoke the requested lumerpy function
# ---------------------------------------------------------------------------


@app.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    logger.debug("call_tool › %s(%s)", name, arguments)

    if not hasattr(lumerpy, name):
        raise ValueError(f"Unknown lumerpy function: {name}")

    fn = getattr(lumerpy, name)
    if not callable(fn):
        raise ValueError(f"Attribute '{name}' exists but is not callable")

    # NOTE: arguments are already deserialised JSON – they may need type
    # conversion if your API expects ints/floats.  For a quick start we pass
    # them verbatim; Python will coerce strings where possible.
    try:
        result = fn(**arguments)
    except Exception as exc:  # noqa: BLE001
        logger.exception("Error inside lumerpy.%s", name)
        # Re‑raise so the SDK wraps it in an MCP‑formatted error message
        raise exc

    text = json.dumps(result, ensure_ascii=False, default=str)
    return [TextContent(type="text", text=text)]


# ---------------------------------------------------------------------------
# entry‑point – run under stdio transport
# ---------------------------------------------------------------------------


async def main() -> None:  # pragma: no cover
    async with stdio_server() as (reader, writer):
        await app.run(reader, writer, app.create_initialization_options())


if __name__ == "__main__":  # pragma: no cover
    asyncio.run(main())
