"""
Pickaxe File System MCP Server

A Model Context Protocol (MCP) server that 
"""

import os
import sys
from fastmcp import FastMCP

mcp = FastMCP(
    name="pickaxe-file-system",
    instructions="This MCP provides access to the file system. You can read, write, and list files. Use the 'read', 'write', and 'list' tools.",
)

@mcp.tool()
def read(filepath: str) -> str:
    """
    Reads the content of a file.
    """
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return f"Error: File '{filepath}' not found."
    except Exception as e:
        return f"Error reading file '{filepath}': {e}"
    
@mcp.tool()
def write(filepath: str, content: str) -> str:
    """
    Writes content to a file. Creates the file if it doesn't exist, overwrites if it does.
    """
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        return f"Successfully wrote to '{filepath}'."
    except Exception as e:
        return f"Error writing to file '{filepath}': {e}"
    
@mcp.tool()
def list_files(directory: str) -> list[str] | str:
    """
    Lists files and directories in a given directory. Defaults to the current directory.
    """
    try:
        return os.listdir(directory)
    except FileNotFoundError:
        return f"Error: Directory '{directory}' not found."
    except Exception as e:
        return f"Error listing directory '{directory}': {e}"

def main():
    if len(sys.argv) > 1:
        path_argument = sys.argv[1]
        print(f"Path argument received: {path_argument}")
    else:
        print("No path argument provided.")

    mcp.run(transport="stdio")

if __name__ == "__main__":
    main()
