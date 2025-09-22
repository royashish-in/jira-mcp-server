# Welcome to FastMCP 2.0!

> The fast, Pythonic way to build MCP servers and clients.

![F logo on a watercolor background](https://mintcdn.com/fastmcp/xdeorzy2A8w9kCCa/assets/brand/f-watercolor-waves.png?fit=max&auto=format&n=xdeorzy2A8w9kCCa&q=85&s=77138c04347ed9726fc34a7ef5e4f21d)

**FastMCP is the standard framework for building MCP applications.** The [Model Context Protocol](https://modelcontextprotocol.io/) (MCP) provides a standardized way to connect LLMs to tools and data, and FastMCP makes it production-ready with clean, Pythonic code:

```python
from fastmcp import FastMCP

mcp = FastMCP("Demo 🚀")

@mcp.tool
def add(a: int, b: int) -> int:
    """Add two numbers"""
    return a + b

if __name__ == "__main__":
    mcp.run()
```

## Beyond Basic MCP

FastMCP pioneered Python MCP development, with FastMCP 1.0 being incorporated into the [official MCP SDK](https://github.com/modelcontextprotocol/python-sdk) in 2024.

**This is FastMCP 2.0** — the actively maintained version that extends far beyond basic protocol implementation. While the SDK provides core functionality, FastMCP 2.0 delivers everything needed for production: advanced MCP patterns (server composition, proxying, OpenAPI/FastAPI generation, tool transformation), enterprise auth (Google, GitHub, Azure, Auth0, WorkOS, and more), deployment tools, testing frameworks, and comprehensive client libraries.

Ready to build? Start with the [installation guide](https://gofastmcp.com/getting-started/installation) or jump straight to the [quickstart](https://gofastmcp.com/getting-started/quickstart).

## What is MCP?

The Model Context Protocol lets you build servers that expose data and functionality to LLM applications in a secure, standardized way. It is often described as "the USB-C port for AI", providing a uniform way to connect LLMs to resources they can use. It may be easier to think of it as an API, but specifically designed for LLM interactions. MCP servers can:

* Expose data through `Resources` (think of these sort of like GET endpoints; they are used to load information into the LLM's context)
* Provide functionality through `Tools` (sort of like POST endpoints; they are used to execute code or otherwise produce a side effect)
* Define interaction patterns through `Prompts` (reusable templates for LLM interactions)
* And more!

FastMCP provides a high-level, Pythonic interface for building, managing, and interacting with these servers.

## Why FastMCP?

FastMCP handles all the complex protocol details so you can focus on building. In most cases, decorating a Python function is all you need — FastMCP handles the rest.

- 🚀 **Fast**: High-level interface means less code and faster development
- 🍀 **Simple**: Build MCP servers with minimal boilerplate
- 🐍 **Pythonic**: Feels natural to Python developers
- 🔍 **Complete**: Everything for production — enterprise auth (Google, GitHub, Azure, Auth0, WorkOS), deployment tools, testing frameworks, client libraries, and more

FastMCP provides the shortest path from idea to production. Deploy locally, to the cloud with [FastMCP Cloud](https://fastmcp.cloud) (free for personal servers), or to your own infrastructure.

FastMCP is made with 💙 by [Prefect](https://www.prefect.io/).

## LLM-Friendly Docs

The FastMCP documentation is available in multiple LLM-friendly formats:

### MCP Server

The FastMCP docs are accessible via MCP! The server URL is `https://gofastmcp.com/mcp`.

You can use FastMCP to search the FastMCP docs:

```python
import asyncio
from fastmcp import Client

async def main():
    async with Client("https://gofastmcp.com/mcp") as client:
        result = await client.call_tool(
            name="SearchFastMcp", 
            arguments={"query": "deploy a FastMCP server"}
        )
    print(result)

asyncio.run(main())
```

### Plain Text Formats

The docs are also available in [llms.txt format](https://llmstxt.org/):

* [llms.txt](https://gofastmcp.com/llms.txt) - A sitemap listing all documentation pages
* [llms-full.txt](https://gofastmcp.com/llms-full.txt) - The entire documentation in one file (may exceed context windows)

Any page can be accessed as markdown by appending `.md` to the URL. For example, this page becomes `https://gofastmcp.com/getting-started/welcome.md`.

You can also copy any page as markdown by pressing "Cmd+C" (or "Ctrl+C" on Windows) on your keyboard.
