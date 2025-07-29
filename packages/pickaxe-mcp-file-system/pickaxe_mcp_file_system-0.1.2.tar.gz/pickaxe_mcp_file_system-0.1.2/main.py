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

allowed_base_paths = []

def validate_path(path_to_check: str) -> str | None:
    """
    Validates if the given path is within the allowed base paths.
    """
    if not allowed_base_paths:
        return "Error: Access restricted. No base paths have been configured for operations."
    
    try:
        # resolve to absolute path to handle relative paths and '..' robustly
        abs_path_to_check = os.path.abspath(path_to_check)
        
        # check if the path is within any of the allowed base paths
        for base_path in allowed_base_paths:
            if abs_path_to_check == base_path or abs_path_to_check.startswith(os.path.join(base_path, '')):
                return None  # path is valid
        
        return f"Error: Access to path '{path_to_check}' is denied. It is outside all allowed directories."
    except Exception as e:
        return f"Error during path validation for '{path_to_check}': {e}"

@mcp.tool()
def read(filepath: str) -> str:
    """
    Reads the content of a file.
    """
    try:
        validation_error = validate_path(filepath)
        if validation_error:
            return validation_error

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
        validation_error = validate_path(filepath)
        if validation_error:
            return validation_error
    
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
        validation_error = validate_path(directory)
        if validation_error:
            return validation_error
    
        return os.listdir(directory)
    except FileNotFoundError:
        return f"Error: Directory '{directory}' not found."
    except Exception as e:
        return f"Error listing directory '{directory}': {e}"

@mcp.tool()
def list_available_directories() -> list[str]:
    """
    Lists all allowed base paths for file operations.
    """
    if not allowed_base_paths:
        return ["No allowed base paths configured."]
    
    return allowed_base_paths

def main():
    global allowed_base_paths
    
    if len(sys.argv) > 1:
        path_arguments = sys.argv[1:]

        valid_paths = []
        for path_arg in path_arguments:
            resolved_path = os.path.abspath(path_arg)

            if os.path.isdir(resolved_path):
                valid_paths.append(resolved_path)
                print(f"Added allowed path: {resolved_path}")
            else:
                print(f"Warning: Path '{path_arg}' (resolved to '{resolved_path}') is not a valid directory. Skipping.")

        if valid_paths:
            allowed_base_paths = valid_paths

    mcp.run(transport="stdio")

if __name__ == "__main__":
    main()
