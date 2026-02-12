"""
Tool Manager - Tool execution with sandboxing and safety controls.

Available Tools:
- calculator: Evaluate mathematical expressions (AST-based, no eval)
- code_execute: Run Python code in a sandboxed subprocess
- json_parse: Parse and query JSON data
"""

import asyncio
import json
import multiprocessing
from pathlib import Path
from typing import Any, Optional


class ToolManager:
    """
    Manages safe execution of tools and external capabilities.
    Includes sandboxing for code execution.
    """

    # Safety limits
    MAX_CODE_EXECUTION_TIME = 10  # seconds
    MAX_OUTPUT_LENGTH = 10000  # characters

    def __init__(self, workspace_dir: str = "workspace"):
        self.workspace = Path(workspace_dir)
        self.workspace.mkdir(exist_ok=True)
        self.available_tools = {}
        self.tool_descriptions = {}
        self._register_default_tools()

    def _register_default_tools(self):
        """Register all available tools with descriptions."""
        self.available_tools = {
            "calculator": self._calculator,
            "code_execute": self._code_execute,
            "json_parse": self._json_parse,
        }

        self.tool_descriptions = {
            "calculator": {
                "description": "Evaluate mathematical expressions safely",
                "params": {"expression": "Mathematical expression to evaluate"},
                "example": "calculator(expression='2 + 2 * 3')",
            },
            "code_execute": {
                "description": "Execute Python code in a sandbox",
                "params": {"code": "Python code to execute"},
                "example": "code_execute(code='print(sum(range(10)))')",
            },
            "json_parse": {
                "description": "Parse JSON and extract data using path",
                "params": {
                    "data": "JSON string or dict",
                    "path": "Dot-notation path (e.g., 'users.0.name')",
                },
                "example": "json_parse(data='{\"a\": 1}', path='a')",
            },
        }

    # ============================================
    # Calculator (AST-based, no eval)
    # ============================================

    def _calculator(self, expression: str) -> dict[str, Any]:
        """
        Safe mathematical expression evaluator using AST.
        Supports: +, -, *, /, **, %, parentheses, and math functions.
        Uses AST parsing instead of eval() for security.
        """
        import ast
        import math
        import operator

        # Allowed operators
        operators = {
            ast.Add: operator.add,
            ast.Sub: operator.sub,
            ast.Mult: operator.mul,
            ast.Div: operator.truediv,
            ast.FloorDiv: operator.floordiv,
            ast.Mod: operator.mod,
            ast.Pow: operator.pow,
            ast.USub: operator.neg,
            ast.UAdd: operator.pos,
        }

        # Allowed functions
        functions = {
            "abs": abs,
            "round": round,
            "min": min,
            "max": max,
            "sum": sum,
            "pow": pow,
            "sqrt": math.sqrt,
            "sin": math.sin,
            "cos": math.cos,
            "tan": math.tan,
            "log": math.log,
            "log10": math.log10,
            "exp": math.exp,
            "floor": math.floor,
            "ceil": math.ceil,
        }

        # Allowed constants
        constants = {
            "pi": math.pi,
            "e": math.e,
        }

        def safe_eval(node):
            """Recursively evaluate AST nodes safely."""
            if isinstance(node, ast.Expression):
                return safe_eval(node.body)
            elif isinstance(node, ast.Constant):  # Python 3.8+
                if isinstance(node.value, (int, float)):
                    return node.value
                raise ValueError(f"Invalid constant: {node.value}")
            elif isinstance(node, ast.Num):  # Python 3.7 compatibility
                return node.n
            elif isinstance(node, ast.Name):
                if node.id in constants:
                    return constants[node.id]
                raise ValueError(f"Unknown variable: {node.id}")
            elif isinstance(node, ast.BinOp):
                op_type = type(node.op)
                if op_type not in operators:
                    raise ValueError(f"Unsupported operator: {op_type.__name__}")
                left = safe_eval(node.left)
                right = safe_eval(node.right)
                return operators[op_type](left, right)
            elif isinstance(node, ast.UnaryOp):
                op_type = type(node.op)
                if op_type not in operators:
                    raise ValueError(f"Unsupported operator: {op_type.__name__}")
                operand = safe_eval(node.operand)
                return operators[op_type](operand)
            elif isinstance(node, ast.Call):
                if not isinstance(node.func, ast.Name):
                    raise ValueError("Only simple function calls allowed")
                func_name = node.func.id
                if func_name not in functions:
                    raise ValueError(f"Unknown function: {func_name}")
                args = [safe_eval(arg) for arg in node.args]
                return functions[func_name](*args)
            else:
                raise ValueError(f"Unsupported expression type: {type(node).__name__}")

        try:
            # Parse expression into AST
            tree = ast.parse(expression, mode="eval")
            result = safe_eval(tree)
            return {"success": True, "result": result, "expression": expression}
        except SyntaxError as e:
            return {"success": False, "error": f"Syntax error: {e}", "expression": expression}
        except ValueError as e:
            return {"success": False, "error": str(e), "expression": expression}
        except ZeroDivisionError:
            return {"success": False, "error": "Division by zero", "expression": expression}
        except Exception as e:
            return {"success": False, "error": str(e), "expression": expression}

    # ============================================
    # Code Execution (Sandboxed via multiprocessing)
    # ============================================

    def _code_execute(self, code: str) -> dict[str, Any]:
        """
        Execute Python code in a restricted sandbox.
        Limited builtins, no file/network access, timeout ENFORCED via multiprocessing.
        """
        # First, compile to catch syntax errors before spawning process
        try:
            compile(code, "<sandbox>", "exec")
        except SyntaxError as e:
            return {"success": False, "error": f"Syntax error: {e}", "line": e.lineno}

        # Use multiprocessing to enforce timeout
        result_queue = multiprocessing.Queue()
        process = multiprocessing.Process(
            target=self._sandbox_worker, args=(code, result_queue, self.MAX_OUTPUT_LENGTH)
        )

        try:
            process.start()
            process.join(timeout=self.MAX_CODE_EXECUTION_TIME)

            if process.is_alive():
                # Process exceeded timeout - kill it
                process.terminate()
                process.join(timeout=1)
                if process.is_alive():
                    process.kill()
                    process.join()
                return {
                    "success": False,
                    "error": f"Execution timed out after {self.MAX_CODE_EXECUTION_TIME} seconds",
                    "timed_out": True,
                }

            # Get result from queue
            if not result_queue.empty():
                return result_queue.get_nowait()
            else:
                return {"success": False, "error": "No result returned from sandbox"}

        except Exception as e:
            return {"success": False, "error": f"Sandbox error: {type(e).__name__}: {str(e)}"}
        finally:
            if process.is_alive():
                process.kill()
                process.join()

    @staticmethod
    def _sandbox_worker(code: str, result_queue: multiprocessing.Queue, max_output: int):
        """
        Worker function that runs in a separate process.
        This provides true isolation and allows the parent to kill it on timeout.
        """
        import io
        import resource
        from contextlib import redirect_stderr, redirect_stdout

        # Set resource limits (Unix only) - prevents memory bombs
        try:
            resource.setrlimit(resource.RLIMIT_AS, (100 * 1024 * 1024, 100 * 1024 * 1024))
            resource.setrlimit(resource.RLIMIT_CPU, (10, 10))
        except (OSError, ValueError):
            pass

        # Restricted builtins - no dangerous operations
        safe_builtins = {
            "abs": abs,
            "all": all,
            "any": any,
            "bin": bin,
            "bool": bool,
            "chr": chr,
            "dict": dict,
            "dir": dir,
            "divmod": divmod,
            "enumerate": enumerate,
            "filter": filter,
            "float": float,
            "format": format,
            "frozenset": frozenset,
            "hash": hash,
            "hex": hex,
            "int": int,
            "isinstance": isinstance,
            "issubclass": issubclass,
            "iter": iter,
            "len": len,
            "list": list,
            "map": map,
            "max": max,
            "min": min,
            "next": next,
            "oct": oct,
            "ord": ord,
            "pow": pow,
            "print": print,
            "range": range,
            "repr": repr,
            "reversed": reversed,
            "round": round,
            "set": set,
            "slice": slice,
            "sorted": sorted,
            "str": str,
            "sum": sum,
            "tuple": tuple,
            "type": type,
            "zip": zip,
            "True": True,
            "False": False,
            "None": None,
        }

        # Safe modules only
        import collections
        import datetime
        import json as json_module
        import math
        import random
        import re as re_module

        safe_modules = {
            "math": math,
            "random": random,
            "datetime": datetime,
            "json": json_module,
            "re": re_module,
            "collections": collections,
        }

        def restricted_import(name, globals=None, locals=None, fromlist=(), level=0):
            if name in safe_modules:
                return safe_modules[name]
            raise ImportError(f"Module '{name}' is not allowed in sandbox")

        safe_builtins["__import__"] = restricted_import

        restricted_globals = {
            "__builtins__": safe_builtins,
            "__name__": "__sandbox__",
            **safe_modules,
        }

        stdout_capture = io.StringIO()
        stderr_capture = io.StringIO()

        try:
            compiled = compile(code, "<sandbox>", "exec")
            with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
                exec(compiled, restricted_globals)

            result_queue.put(
                {
                    "success": True,
                    "stdout": stdout_capture.getvalue()[:max_output],
                    "stderr": stderr_capture.getvalue()[:max_output],
                    "has_output": bool(stdout_capture.getvalue() or stderr_capture.getvalue()),
                }
            )
        except Exception as e:
            result_queue.put({"success": False, "error": f"{type(e).__name__}: {str(e)}"})

    # ============================================
    # JSON Parser
    # ============================================

    def _json_parse(self, data: str | dict, path: str = "") -> dict[str, Any]:
        """
        Parse JSON and extract data using dot notation.
        Path examples: 'users.0.name', 'config.settings.theme'
        """
        try:
            if isinstance(data, str):
                parsed = json.loads(data)
            else:
                parsed = data

            if path:
                result = parsed
                for key in path.split("."):
                    if isinstance(result, dict):
                        result = result[key]
                    elif isinstance(result, list):
                        result = result[int(key)]
                    else:
                        return {
                            "success": False,
                            "error": f"Cannot traverse into {type(result).__name__}",
                        }
            else:
                result = parsed

            return {
                "success": True,
                "path": path or "(root)",
                "result": result,
                "type": type(result).__name__,
            }

        except json.JSONDecodeError as e:
            return {"success": False, "error": f"Invalid JSON: {e}"}
        except (KeyError, IndexError) as e:
            return {"success": False, "error": f"Path not found: {e}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ============================================
    # Tool Execution Interface
    # ============================================

    def execute(self, tool_name: str, **kwargs) -> dict[str, Any]:
        """Execute a tool safely."""
        if tool_name not in self.available_tools:
            return {
                "success": False,
                "error": f"Tool '{tool_name}' not found",
                "available_tools": list(self.available_tools.keys()),
            }

        try:
            tool_func = self.available_tools[tool_name]
            return tool_func(**kwargs)
        except TypeError as e:
            desc = self.tool_descriptions.get(tool_name, {})
            return {
                "success": False,
                "error": f"Invalid arguments: {e}",
                "expected_params": desc.get("params", {}),
                "example": desc.get("example", ""),
            }
        except Exception as e:
            return {"success": False, "error": f"Tool execution failed: {str(e)}"}

    async def execute_async(self, tool_name: str, **kwargs) -> dict[str, Any]:
        """Execute a tool asynchronously (runs in thread pool)."""
        return await asyncio.to_thread(self.execute, tool_name, **kwargs)

    def list_tools(self) -> list[str]:
        """List available tools."""
        return list(self.available_tools.keys())

    def get_tool_info(self, tool_name: str) -> Optional[dict]:
        """Get detailed info about a tool."""
        if tool_name not in self.tool_descriptions:
            return None
        return self.tool_descriptions[tool_name]

    def get_all_tool_info(self) -> dict[str, dict]:
        """Get info about all tools."""
        return self.tool_descriptions.copy()

    def register_tool(
        self, name: str, func, description: str, params: dict[str, str], example: str
    ):
        """Register a custom tool."""
        self.available_tools[name] = func
        self.tool_descriptions[name] = {
            "description": description,
            "params": params,
            "example": example,
        }
