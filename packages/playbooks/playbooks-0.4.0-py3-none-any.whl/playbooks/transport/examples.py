"""Examples demonstrating the transport layer usage."""

import asyncio
import logging
from typing import Any, Dict

from .mcp_transport import MCPTransport
from .protocol import TransportProtocol

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def example_mcp_transport():
    """Example of using MCPTransport to connect to an MCP server."""

    # Example configuration for an MCP server
    config = {
        "url": "http://localhost:8000/mcp",  # SSE endpoint
        "transport": "sse",
        "timeout": 30.0,
    }

    # Create and use the transport
    transport = MCPTransport(config)

    try:
        # Connect to the server
        await transport.connect()
        logger.info("Connected to MCP server")

        # List available tools
        tools = await transport.list_tools()
        logger.info(
            f"Available tools: {[tool.get('name', 'unnamed') for tool in tools]}"
        )

        # List available resources
        resources = await transport.list_resources()
        logger.info(f"Available resources: {len(resources)} resources found")

        # Example tool call (if tools are available)
        if tools:
            first_tool = tools[0]
            tool_name = first_tool.get("name")
            if tool_name:
                logger.info(f"Calling tool: {tool_name}")
                try:
                    result = await transport.call_tool(tool_name, {})
                    logger.info(f"Tool result: {result}")
                except Exception as e:
                    logger.warning(f"Tool call failed: {e}")

    except ConnectionError as e:
        logger.error(f"Connection failed: {e}")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
    finally:
        # Always disconnect
        await transport.disconnect()
        logger.info("Disconnected from MCP server")


async def example_stdio_transport():
    """Example of using MCPTransport with stdio transport."""

    # Example configuration for a stdio MCP server
    config = {
        "url": "path/to/mcp_server.py",  # Path to MCP server script
        "transport": "stdio",
        "timeout": 30.0,
    }

    transport = MCPTransport(config)

    try:
        await transport.connect()
        logger.info("Connected to stdio MCP server")

        # Test basic connectivity
        await transport.call("ping")
        logger.info("Ping successful")

        # List tools
        tools = await transport.list_tools()
        logger.info(f"Found {len(tools)} tools")

    except Exception as e:
        logger.error(f"Stdio transport example failed: {e}")
    finally:
        await transport.disconnect()


async def example_context_manager():
    """Example using transport as an async context manager."""

    config = {"url": "http://localhost:8000/mcp", "transport": "sse"}

    # Use transport as context manager for automatic connection/disconnection
    async with MCPTransport(config) as transport:
        logger.info("Connected via context manager")

        # Use the transport
        tools = await transport.list_tools()
        logger.info(f"Tools: {len(tools)}")

        # Context manager will automatically disconnect


def example_transport_factory(config: Dict[str, Any]) -> TransportProtocol:
    """Example factory function for creating transports based on configuration."""

    transport_type = config.get("type", "mcp")

    if transport_type == "mcp":
        return MCPTransport(config)
    else:
        raise ValueError(f"Unsupported transport type: {transport_type}")


if __name__ == "__main__":
    # Run the examples
    print("Running MCP Transport Examples...")

    # Note: These examples assume you have an MCP server running
    # You can create a simple test server using FastMCP for testing

    try:
        asyncio.run(example_mcp_transport())
    except KeyboardInterrupt:
        print("Example interrupted by user")
    except Exception as e:
        print(f"Example failed: {e}")
        print(
            "Note: Make sure you have an MCP server running for these examples to work"
        )
