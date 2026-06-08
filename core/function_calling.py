"""
Function Calling & Tool Parameter Passing Layer

Enables structured tool use with parameter schemas, validation, and result handling.
Transforms execution from app-only to general function calling support.
"""
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass
import json

@dataclass
class ToolParameter:
    """Defines a single parameter for a tool."""
    name: str
    type: str  # "string", "number", "boolean", "array"
    description: str
    required: bool = True
    enum: Optional[List[str]] = None


@dataclass
class ToolSchema:
    """Defines the schema for a callable tool/function."""
    name: str
    description: str
    parameters: List[ToolParameter]
    return_type: str = "string"


class ToolRegistry:
    """Centralized registry of callable tools with schemas."""
    
    _tools: Dict[str, Dict[str, Any]] = {}
    
    @classmethod
    def register_tool(cls, schema: ToolSchema, implementation: Callable):
        """Registers a tool with its schema and implementation."""
        cls._tools[schema.name] = {
            "schema": schema,
            "implementation": implementation
        }
        print(f"🔌 [TOOL REGISTRY]: Registered tool '{schema.name}'")
    
    @classmethod
    def get_tool(cls, tool_name: str) -> Optional[Dict[str, Any]]:
        """Retrieves a tool by name."""
        return cls._tools.get(tool_name)
    
    @classmethod
    def get_all_tools(cls) -> Dict[str, ToolSchema]:
        """Returns schemas for all registered tools (for LLM awareness)."""
        return {name: tool["schema"] for name, tool in cls._tools.items()}
    
    @classmethod
    def list_tool_schemas(cls) -> str:
        """Returns formatted tool schemas for system prompt injection."""
        schemas = []
        for name, tool in cls._tools.items():
            schema = tool["schema"]
            params = []
            for param in schema.parameters:
                param_str = f"  - {param.name} ({param.type}): {param.description}"
                if not param.required:
                    param_str += " [OPTIONAL]"
                params.append(param_str)
            
            schema_str = f"""
### {schema.name}
{schema.description}

**Parameters:**
{chr(10).join(params)}

**Returns:** {schema.return_type}
"""
            schemas.append(schema_str)
        
        return "\n".join(schemas)


class FunctionCaller:
    """Handles function call execution, parameter validation, and result integration."""
    
    @staticmethod
    def validate_parameters(tool_name: str, params: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """
        Validates parameters against the tool schema.
        
        Returns:
            (is_valid, error_message)
        """
        tool = ToolRegistry.get_tool(tool_name)
        if not tool:
            return False, f"Tool '{tool_name}' not found"
        
        schema = tool["schema"]
        
        # Check required parameters
        for param in schema.parameters:
            if param.required and param.name not in params:
                return False, f"Required parameter missing: {param.name}"
        
        # Validate parameter types
        for param in schema.parameters:
            if param.name not in params:
                continue
            
            value = params[param.name]
            
            if param.type == "string" and not isinstance(value, str):
                return False, f"Parameter '{param.name}' must be a string"
            elif param.type == "number" and not isinstance(value, (int, float)):
                return False, f"Parameter '{param.name}' must be a number"
            elif param.type == "boolean" and not isinstance(value, bool):
                return False, f"Parameter '{param.name}' must be a boolean"
            elif param.type == "array" and not isinstance(value, list):
                return False, f"Parameter '{param.name}' must be an array"
            
            # Check enum constraints
            if param.enum and value not in param.enum:
                return False, f"Parameter '{param.name}' must be one of: {param.enum}"
        
        return True, None
    
    @staticmethod
    def call_tool(tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calls a tool with validated parameters.
        
        Returns:
            {"success": bool, "result": Any, "error": Optional[str]}
        """
        # Validate
        is_valid, error = FunctionCaller.validate_parameters(tool_name, params)
        if not is_valid:
            return {
                "success": False,
                "result": None,
                "error": error
            }
        
        try:
            # Get tool
            tool = ToolRegistry.get_tool(tool_name)
            if not tool:
                return {
                    "success": False,
                    "result": None,
                    "error": f"Tool '{tool_name}' not found"
                }
            
            # Execute
            result = tool["implementation"](**params)
            
            return {
                "success": True,
                "result": result,
                "error": None
            }
        
        except Exception as e:
            return {
                "success": False,
                "result": None,
                "error": f"Tool execution failed: {str(e)}"
            }
    
    @staticmethod
    def parse_tool_call(response_text: str) -> Optional[Dict[str, Any]]:
        """
        Attempts to parse a tool call from LLM response.
        
        Expects format:
        TOOL_CALL: {
          "tool": "tool_name",
          "parameters": {
            "param1": "value1",
            "param2": "value2"
          }
        }
        
        Returns:
            {"tool": str, "parameters": dict} or None
        """
        import re
        
        # Look for tool call marker
        match = re.search(r'TOOL_CALL:\s*(\{[\s\S]*?\})', response_text)
        if not match:
            return None
        
        try:
            json_str = match.group(1)
            # Find the closing brace
            open_braces = 0
            for i, char in enumerate(json_str):
                if char == '{':
                    open_braces += 1
                elif char == '}':
                    open_braces -= 1
                    if open_braces == 0:
                        json_str = json_str[:i+1]
                        break
            
            call = json.loads(json_str)
            return {
                "tool": call.get("tool"),
                "parameters": call.get("parameters", {})
            }
        except (json.JSONDecodeError, AttributeError):
            return None


# ==============================================================================
# BUILT-IN TOOL IMPLEMENTATIONS
# ==============================================================================

def tool_get_file_content(file_path: str) -> str:
    """Reads and returns the content of a file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return f"Error reading file: {str(e)}"


def tool_write_file(file_path: str, content: str) -> str:
    """Writes content to a file."""
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return f"File written successfully: {file_path}"
    except Exception as e:
        return f"Error writing file: {str(e)}"


def tool_list_directory(directory_path: str) -> List[str]:
    """Lists files and directories in a path."""
    try:
        import os
        return os.listdir(directory_path)
    except Exception as e:
        return [f"Error listing directory: {str(e)}"]


def tool_search_files(directory: str, pattern: str) -> List[str]:
    """Searches for files matching a pattern in a directory."""
    try:
        import os
        import re
        results = []
        for root, dirs, files in os.walk(directory):
            for file in files:
                if re.search(pattern, file):
                    results.append(os.path.join(root, file))
        return results
    except Exception as e:
        return [f"Error searching files: {str(e)}"]


def tool_execute_command(command: str) -> str:
    """Executes a shell command and returns output."""
    try:
        import subprocess
        result = subprocess.run(command, capture_output=True, text=True, timeout=10)
        return result.stdout or result.stderr
    except Exception as e:
        return f"Error executing command: {str(e)}"


# ==============================================================================
# INITIALIZE BUILT-IN TOOLS
# ==============================================================================

def initialize_builtin_tools():
    """Registers all built-in tools."""
    
    # Tool: Read File
    ToolRegistry.register_tool(
        ToolSchema(
            name="read_file",
            description="Reads the entire content of a file",
            parameters=[
                ToolParameter("file_path", "string", "Absolute or relative path to the file", required=True)
            ],
            return_type="string"
        ),
        tool_get_file_content
    )
    
    # Tool: Write File
    ToolRegistry.register_tool(
        ToolSchema(
            name="write_file",
            description="Writes content to a file (creates or overwrites)",
            parameters=[
                ToolParameter("file_path", "string", "Path where to write the file", required=True),
                ToolParameter("content", "string", "The content to write", required=True)
            ],
            return_type="string"
        ),
        tool_write_file
    )
    
    # Tool: List Directory
    ToolRegistry.register_tool(
        ToolSchema(
            name="list_directory",
            description="Lists all files and subdirectories in a path",
            parameters=[
                ToolParameter("directory_path", "string", "Path to the directory", required=True)
            ],
            return_type="array"
        ),
        tool_list_directory
    )
    
    # Tool: Search Files
    ToolRegistry.register_tool(
        ToolSchema(
            name="search_files",
            description="Searches for files matching a regex pattern",
            parameters=[
                ToolParameter("directory", "string", "Directory to search in", required=True),
                ToolParameter("pattern", "string", "Regex pattern to match", required=True)
            ],
            return_type="array"
        ),
        tool_search_files
    )
    
    # Tool: Execute Command
    ToolRegistry.register_tool(
        ToolSchema(
            name="execute_command",
            description="Executes a shell command and returns output",
            parameters=[
                ToolParameter("command", "string", "The command to execute", required=True)
            ],
            return_type="string"
        ),
        tool_execute_command
    )
    
    print("[Tool Registry] 5 built-in tools initialized")
