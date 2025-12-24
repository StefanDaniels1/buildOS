"""
Custom MCP Tools Server

Creates a dynamic MCP server from enabled custom tools.
Tools are loaded from SQLite and compiled at runtime.
"""

import json
import os
import traceback
from typing import Dict, Any, Callable, List

from claude_agent_sdk import tool, create_sdk_mcp_server
from .loader import load_enabled_tools


def create_tool_handler(tool_def: Dict[str, Any]) -> Callable:
    """
    Create an async tool handler from tool definition.

    The handler_code should define an async function with the same name as the tool.
    Example:
        async def my_tool(args: dict) -> dict:
            return {"success": True, "data": args}
    """
    code = tool_def["handler_code"]
    tool_name = tool_def["name"]
    env_vars = tool_def.get("env_vars", {})

    # Set environment variables for this tool
    for key, value in env_vars.items():
        if value:  # Only set non-empty values
            os.environ[key] = value

    # Create execution context with safe imports
    exec_globals = {
        "__builtins__": __builtins__,
        "json": __import__("json"),
        "os": __import__("os"),
        "Path": __import__("pathlib").Path,
    }

    # Try to import optional dependencies
    try:
        exec_globals["httpx"] = __import__("httpx")
    except ImportError:
        pass

    try:
        exec_globals["aiohttp"] = __import__("aiohttp")
    except ImportError:
        pass

    try:
        exec_globals["requests"] = __import__("requests")
    except ImportError:
        pass

    # Compile and execute the handler code
    try:
        exec(code, exec_globals)
    except Exception as e:
        raise ValueError(f"Failed to compile tool '{tool_name}': {e}")

    # Get the handler function
    handler = exec_globals.get(tool_name)
    if not handler:
        raise ValueError(
            f"Handler function '{tool_name}' not found in code. "
            f"Make sure the function name matches the tool name."
        )

    if not callable(handler):
        raise ValueError(f"'{tool_name}' is not a callable function")

    # Wrap with error handling and MCP response format
    async def wrapped_handler(args: Dict[str, Any]) -> Dict[str, Any]:
        try:
            result = await handler(args)

            # Ensure result is properly formatted for MCP
            if isinstance(result, dict):
                return {
                    "content": [{
                        "type": "text",
                        "text": json.dumps(result, indent=2, default=str)
                    }]
                }
            else:
                return {
                    "content": [{
                        "type": "text",
                        "text": str(result)
                    }]
                }

        except Exception as e:
            error_response = {
                "success": False,
                "error": str(e),
                "traceback": traceback.format_exc()
            }
            return {
                "content": [{
                    "type": "text",
                    "text": json.dumps(error_response, indent=2)
                }],
                "is_error": True
            }

    return wrapped_handler


def convert_schema_to_types(input_schema: Dict[str, str]) -> Dict[str, Any]:
    """
    Convert simplified schema to Python types for the @tool decorator.

    Input schema format: {"param_name": "type_string"}
    Type strings: "str", "int", "float", "bool", "list", "dict"
    """
    type_map = {
        "str": str,
        "string": str,
        "int": int,
        "integer": int,
        "float": float,
        "number": float,
        "bool": bool,
        "boolean": bool,
        "list": list,
        "array": list,
        "dict": dict,
        "object": dict,
    }

    result = {}
    for param_name, type_str in input_schema.items():
        type_str_lower = type_str.lower()
        result[param_name] = type_map.get(type_str_lower, str)

    return result


def create_custom_tools_server(server_name: str = "custom"):
    """
    Create an MCP server with all enabled custom tools.

    Returns None if no custom tools are enabled.
    """
    enabled_tools = load_enabled_tools()

    if not enabled_tools:
        print(f"No enabled custom tools found")
        return None

    print(f"Loading {len(enabled_tools)} custom tools...")

    tool_functions = []
    for tool_def in enabled_tools:
        try:
            # Create the handler
            handler = create_tool_handler(tool_def)

            # Convert schema
            schema = convert_schema_to_types(tool_def["input_schema"])

            # Create decorated tool
            decorated = tool(
                name=tool_def["name"],
                description=tool_def["description"],
                input_schema=schema
            )(handler)

            tool_functions.append(decorated)
            print(f"  - Loaded tool: {tool_def['name']}")

        except Exception as e:
            print(f"  - Failed to load tool '{tool_def['name']}': {e}")
            continue

    if not tool_functions:
        print("No tools successfully loaded")
        return None

    # Create the MCP server
    server = create_sdk_mcp_server(
        name=server_name,
        version="1.0.0",
        tools=tool_functions
    )

    print(f"Custom tools server '{server_name}' created with {len(tool_functions)} tools")
    return server


def get_custom_tool_names() -> List[str]:
    """Get list of enabled custom tool names for allowed_tools config."""
    tools = load_enabled_tools()
    return [f"mcp__custom__{t['name']}" for t in tools]
