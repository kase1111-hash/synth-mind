"""
Tool Manager - Advanced tool execution with sandboxing and safety controls.

Available Tools:
- calculator: Evaluate mathematical expressions
- timer: Wait for specified seconds
- web_search: Search the web using DuckDuckGo
- http_fetch: Fetch content from URLs
- code_execute: Run Python code in a sandbox
- file_read: Read files from workspace
- file_write: Write files to workspace
- file_list: List files in workspace
- shell_run: Execute shell commands (restricted)
- json_parse: Parse and query JSON data
"""

import asyncio
import json
import multiprocessing
import re
import shlex
import subprocess
import time
from pathlib import Path
from typing import Any, Optional
from urllib.parse import quote_plus


class ToolManager:
    """
    Manages safe execution of tools and external capabilities.
    Includes sandboxing for code execution and file operations.
    """

    # Safety limits
    MAX_CODE_EXECUTION_TIME = 10  # seconds
    MAX_OUTPUT_LENGTH = 10000  # characters
    MAX_FILE_SIZE = 1_000_000  # 1MB
    # Safe commands only - removed 'find' (has -exec) and 'grep' (complex args)
    ALLOWED_SHELL_COMMANDS = {
        "ls", "pwd", "date", "whoami", "echo", "head", "tail",
        "wc", "sort", "uniq", "diff", "which"
    }

    # Dangerous argument patterns per command
    BLOCKED_ARGS = {
        "ls": {"-R"},  # Recursive could be slow
        "head": set(),
        "tail": set(),
        "diff": set(),
    }

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
            "timer": self._timer,
            "web_search": self._web_search,
            "http_fetch": self._http_fetch,
            "code_execute": self._code_execute,
            "file_read": self._file_read,
            "file_write": self._file_write,
            "file_list": self._file_list,
            "shell_run": self._shell_run,
            "json_parse": self._json_parse,
        }

        self.tool_descriptions = {
            "calculator": {
                "description": "Evaluate mathematical expressions safely",
                "params": {"expression": "Mathematical expression to evaluate"},
                "example": "calculator(expression='2 + 2 * 3')"
            },
            "timer": {
                "description": "Wait for specified seconds (max 30)",
                "params": {"seconds": "Number of seconds to wait"},
                "example": "timer(seconds=5)"
            },
            "web_search": {
                "description": "Search the web using DuckDuckGo",
                "params": {
                    "query": "Search query",
                    "max_results": "Maximum results to return (default 5)"
                },
                "example": "web_search(query='python async tutorial')"
            },
            "http_fetch": {
                "description": "Fetch content from a URL",
                "params": {
                    "url": "URL to fetch",
                    "extract_text": "Extract text only (default True)"
                },
                "example": "http_fetch(url='https://example.com')"
            },
            "code_execute": {
                "description": "Execute Python code in a sandbox",
                "params": {"code": "Python code to execute"},
                "example": "code_execute(code='print(sum(range(10)))')"
            },
            "file_read": {
                "description": "Read a file from the workspace",
                "params": {"path": "Relative path within workspace"},
                "example": "file_read(path='notes.txt')"
            },
            "file_write": {
                "description": "Write content to a file in the workspace",
                "params": {
                    "path": "Relative path within workspace",
                    "content": "Content to write"
                },
                "example": "file_write(path='output.txt', content='Hello')"
            },
            "file_list": {
                "description": "List files in the workspace",
                "params": {"path": "Relative directory path (default '.')"},
                "example": "file_list(path='.')"
            },
            "shell_run": {
                "description": "Run safe shell commands",
                "params": {"command": "Shell command to execute"},
                "example": "shell_run(command='ls -la')"
            },
            "json_parse": {
                "description": "Parse JSON and extract data using path",
                "params": {
                    "data": "JSON string or dict",
                    "path": "Dot-notation path (e.g., 'users.0.name')"
                },
                "example": "json_parse(data='{\"a\": 1}', path='a')"
            },
        }

    # ============================================
    # Basic Tools
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
            tree = ast.parse(expression, mode='eval')
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

    def _timer(self, seconds: int) -> dict[str, Any]:
        """Timer tool with maximum limit. Uses asyncio-compatible sleep when possible."""
        seconds = min(max(0, seconds), 30)  # 0-30 seconds

        # Check if we're in an async context and use non-blocking sleep
        try:
            loop = asyncio.get_running_loop()
            # We're in an async context - schedule sleep without blocking
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                pool.submit(time.sleep, seconds).result()
        except RuntimeError:
            # No running event loop - safe to use blocking sleep
            time.sleep(seconds)

        return {"success": True, "elapsed": seconds}

    # ============================================
    # Web Tools
    # ============================================

    def _web_search(
        self, query: str, max_results: int = 5
    ) -> dict[str, Any]:
        """
        Search the web using DuckDuckGo Instant Answer API.
        No API key required.
        """
        try:
            import httpx
        except ImportError:
            return {
                "success": False,
                "error": "httpx not installed. Run: pip install httpx"
            }

        try:
            # DuckDuckGo Instant Answer API
            url = f"https://api.duckduckgo.com/?q={quote_plus(query)}&format=json&no_html=1"

            with httpx.Client(timeout=10.0) as client:
                response = client.get(url)
                data = response.json()

            results = []

            # Abstract (main answer)
            if data.get("Abstract"):
                results.append({
                    "title": data.get("Heading", "Answer"),
                    "snippet": data["Abstract"][:500],
                    "url": data.get("AbstractURL", ""),
                    "source": data.get("AbstractSource", "DuckDuckGo")
                })

            # Related topics
            for topic in data.get("RelatedTopics", [])[:max_results]:
                if isinstance(topic, dict) and topic.get("Text"):
                    results.append({
                        "title": topic.get("Text", "")[:100],
                        "snippet": topic.get("Text", "")[:300],
                        "url": topic.get("FirstURL", ""),
                        "source": "DuckDuckGo"
                    })

            # Results (if available)
            for result in data.get("Results", [])[:max_results]:
                results.append({
                    "title": result.get("Text", "")[:100],
                    "snippet": result.get("Text", "")[:300],
                    "url": result.get("FirstURL", ""),
                    "source": "DuckDuckGo"
                })

            return {
                "success": True,
                "query": query,
                "results": results[:max_results],
                "total_found": len(results)
            }

        except Exception as e:
            return {"success": False, "error": str(e), "query": query}

    def _http_fetch(
        self, url: str, extract_text: bool = True
    ) -> dict[str, Any]:
        """
        Fetch content from a URL.
        Optionally extracts text only (removes HTML tags).
        """
        try:
            import httpx
        except ImportError:
            return {
                "success": False,
                "error": "httpx not installed. Run: pip install httpx"
            }

        # Validate URL
        if not url.startswith(("http://", "https://")):
            return {"success": False, "error": "Invalid URL scheme"}

        try:
            headers = {
                "User-Agent": "SynthMind/1.0 (Educational AI Agent)"
            }

            with httpx.Client(timeout=15.0, follow_redirects=True) as client:
                response = client.get(url, headers=headers)

            content = response.text[:self.MAX_OUTPUT_LENGTH]
            content_type = response.headers.get("content-type", "")

            if extract_text and "text/html" in content_type:
                # Simple HTML tag removal
                text = re.sub(r'<script[^>]*>.*?</script>', '', content, flags=re.DOTALL)
                text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL)
                text = re.sub(r'<[^>]+>', ' ', text)
                text = re.sub(r'\s+', ' ', text).strip()
                content = text[:self.MAX_OUTPUT_LENGTH]

            return {
                "success": True,
                "url": url,
                "status_code": response.status_code,
                "content_type": content_type,
                "content": content,
                "length": len(content)
            }

        except httpx.TimeoutException:
            return {"success": False, "error": "Request timed out", "url": url}
        except Exception as e:
            return {"success": False, "error": str(e), "url": url}

    # ============================================
    # Code Execution (Sandboxed)
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
            return {
                "success": False,
                "error": f"Syntax error: {e}",
                "line": e.lineno
            }

        # Use multiprocessing to enforce timeout
        result_queue = multiprocessing.Queue()
        process = multiprocessing.Process(
            target=self._sandbox_worker,
            args=(code, result_queue, self.MAX_OUTPUT_LENGTH)
        )

        try:
            process.start()
            # ACTUALLY ENFORCE TIMEOUT - this was missing before!
            process.join(timeout=self.MAX_CODE_EXECUTION_TIME)

            if process.is_alive():
                # Process exceeded timeout - kill it
                process.terminate()
                process.join(timeout=1)
                if process.is_alive():
                    # Force kill if still running
                    process.kill()
                    process.join()
                return {
                    "success": False,
                    "error": f"Execution timed out after {self.MAX_CODE_EXECUTION_TIME} seconds",
                    "timed_out": True
                }

            # Get result from queue
            if not result_queue.empty():
                return result_queue.get_nowait()
            else:
                return {
                    "success": False,
                    "error": "No result returned from sandbox"
                }

        except Exception as e:
            return {
                "success": False,
                "error": f"Sandbox error: {type(e).__name__}: {str(e)}"
            }
        finally:
            # Ensure process is cleaned up
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
            # Limit memory to 100MB
            resource.setrlimit(resource.RLIMIT_AS, (100 * 1024 * 1024, 100 * 1024 * 1024))
            # Limit CPU time to 10 seconds
            resource.setrlimit(resource.RLIMIT_CPU, (10, 10))
        except (OSError, ValueError):
            pass  # Not available on all systems

        # Restricted builtins - no dangerous operations
        safe_builtins = {
            "abs": abs, "all": all, "any": any, "bin": bin,
            "bool": bool, "chr": chr, "dict": dict, "dir": dir,
            "divmod": divmod, "enumerate": enumerate, "filter": filter,
            "float": float, "format": format, "frozenset": frozenset,
            "hash": hash, "hex": hex, "int": int, "isinstance": isinstance,
            "issubclass": issubclass, "iter": iter, "len": len,
            "list": list, "map": map, "max": max, "min": min,
            "next": next, "oct": oct, "ord": ord, "pow": pow,
            "print": print, "range": range, "repr": repr, "reversed": reversed,
            "round": round, "set": set, "slice": slice, "sorted": sorted,
            "str": str, "sum": sum, "tuple": tuple, "type": type,
            "zip": zip,
            "True": True, "False": False, "None": None,
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

        # Restricted import that only allows safe modules
        def restricted_import(name, globals=None, locals=None, fromlist=(), level=0):
            if name in safe_modules:
                return safe_modules[name]
            raise ImportError(f"Module '{name}' is not allowed in sandbox")

        # Add restricted import to builtins
        safe_builtins["__import__"] = restricted_import

        restricted_globals = {
            "__builtins__": safe_builtins,
            "__name__": "__sandbox__",
            **safe_modules
        }

        stdout_capture = io.StringIO()
        stderr_capture = io.StringIO()

        try:
            compiled = compile(code, "<sandbox>", "exec")
            with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
                exec(compiled, restricted_globals)

            result_queue.put({
                "success": True,
                "stdout": stdout_capture.getvalue()[:max_output],
                "stderr": stderr_capture.getvalue()[:max_output],
                "has_output": bool(stdout_capture.getvalue() or stderr_capture.getvalue())
            })
        except Exception as e:
            result_queue.put({
                "success": False,
                "error": f"{type(e).__name__}: {str(e)}"
            })

    # ============================================
    # File Operations (Sandboxed to workspace)
    # ============================================

    def _validate_path(self, path: str) -> Optional[Path]:
        """Validate path is within workspace."""
        try:
            # Resolve to absolute path
            target = (self.workspace / path).resolve()
            # Ensure it's within workspace
            if self.workspace.resolve() in target.parents or target == self.workspace.resolve():
                return target
            if target.is_relative_to(self.workspace.resolve()):
                return target
            return None
        except Exception:
            return None

    def _file_read(self, path: str) -> dict[str, Any]:
        """Read a file from the workspace directory."""
        target = self._validate_path(path)
        if not target:
            return {"success": False, "error": "Path outside workspace"}

        if not target.exists():
            return {"success": False, "error": f"File not found: {path}"}

        if not target.is_file():
            return {"success": False, "error": f"Not a file: {path}"}

        try:
            size = target.stat().st_size
            if size > self.MAX_FILE_SIZE:
                return {
                    "success": False,
                    "error": f"File too large ({size} bytes, max {self.MAX_FILE_SIZE})"
                }

            content = target.read_text(encoding="utf-8")
            return {
                "success": True,
                "path": path,
                "content": content[:self.MAX_OUTPUT_LENGTH],
                "size": size,
                "truncated": size > self.MAX_OUTPUT_LENGTH
            }
        except UnicodeDecodeError:
            return {"success": False, "error": "Binary file cannot be read as text"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _file_write(self, path: str, content: str) -> dict[str, Any]:
        """Write content to a file in the workspace directory."""
        target = self._validate_path(path)
        if not target:
            return {"success": False, "error": "Path outside workspace"}

        try:
            # Create parent directories if needed
            target.parent.mkdir(parents=True, exist_ok=True)

            # Write content
            target.write_text(content, encoding="utf-8")

            return {
                "success": True,
                "path": path,
                "size": len(content),
                "absolute_path": str(target)
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _file_list(self, path: str = ".") -> dict[str, Any]:
        """List files and directories in the workspace."""
        target = self._validate_path(path)
        if not target:
            return {"success": False, "error": "Path outside workspace"}

        if not target.exists():
            return {"success": False, "error": f"Directory not found: {path}"}

        if not target.is_dir():
            return {"success": False, "error": f"Not a directory: {path}"}

        try:
            items = []
            for item in sorted(target.iterdir()):
                rel_path = item.relative_to(self.workspace)
                items.append({
                    "name": item.name,
                    "path": str(rel_path),
                    "type": "directory" if item.is_dir() else "file",
                    "size": item.stat().st_size if item.is_file() else None
                })

            return {
                "success": True,
                "path": path,
                "items": items,
                "count": len(items)
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ============================================
    # Shell Commands (Restricted)
    # ============================================

    def _shell_run(self, command: str) -> dict[str, Any]:
        """
        Run restricted shell commands safely.
        Uses list-based execution to prevent command injection.
        Only allows safe, read-only commands.
        """
        # Parse command using shlex for proper shell-like tokenization
        try:
            parts = shlex.split(command)
        except ValueError as e:
            return {"success": False, "error": f"Invalid command syntax: {e}"}

        if not parts:
            return {"success": False, "error": "Empty command"}

        base_cmd = parts[0]

        # Check if command is allowed
        if base_cmd not in self.ALLOWED_SHELL_COMMANDS:
            return {
                "success": False,
                "error": f"Command '{base_cmd}' not allowed. Allowed: {', '.join(sorted(self.ALLOWED_SHELL_COMMANDS))}"
            }

        # Validate each argument for dangerous patterns
        dangerous_patterns = [
            r'\.\.',           # Parent directory traversal
            r'^/etc/',         # Sensitive system paths
            r'^/root/',
            r'^/home/',
            r'^/proc/',
            r'^/sys/',
            r'^/dev/',
        ]

        for arg in parts[1:]:
            # Check for dangerous path patterns
            for pattern in dangerous_patterns:
                if re.search(pattern, arg):
                    return {
                        "success": False,
                        "error": f"Argument contains disallowed path pattern: {arg}"
                    }

            # Validate paths are within workspace for file-accessing commands
            if base_cmd in {"head", "tail", "wc", "sort", "uniq", "diff"}:
                if arg.startswith('-'):
                    # It's a flag, check if it's blocked
                    blocked = self.BLOCKED_ARGS.get(base_cmd, set())
                    if arg in blocked:
                        return {
                            "success": False,
                            "error": f"Argument '{arg}' not allowed for {base_cmd}"
                        }
                elif not arg.startswith('-'):
                    # It's a file path - validate it's in workspace
                    validated_path = self._validate_path(arg)
                    if validated_path is None:
                        return {
                            "success": False,
                            "error": f"Path must be within workspace: {arg}"
                        }

        try:
            # SECURITY: Use list-based execution, NOT shell=True
            result = subprocess.run(
                parts,  # List of arguments, not a string
                shell=False,  # CRITICAL: Never use shell=True with user input
                capture_output=True,
                text=True,
                timeout=10,
                cwd=str(self.workspace)
            )

            return {
                "success": result.returncode == 0,
                "command": command,
                "stdout": result.stdout[:self.MAX_OUTPUT_LENGTH],
                "stderr": result.stderr[:self.MAX_OUTPUT_LENGTH],
                "return_code": result.returncode
            }

        except subprocess.TimeoutExpired:
            return {"success": False, "error": "Command timed out", "command": command}
        except FileNotFoundError:
            return {"success": False, "error": f"Command not found: {base_cmd}", "command": command}
        except Exception as e:
            return {"success": False, "error": str(e), "command": command}

    # ============================================
    # Data Tools
    # ============================================

    def _json_parse(
        self, data: str | dict, path: str = ""
    ) -> dict[str, Any]:
        """
        Parse JSON and extract data using dot notation.
        Path examples: 'users.0.name', 'config.settings.theme'
        """
        try:
            # Parse if string
            if isinstance(data, str):
                parsed = json.loads(data)
            else:
                parsed = data

            # Navigate path
            if path:
                result = parsed
                for key in path.split('.'):
                    if isinstance(result, dict):
                        result = result[key]
                    elif isinstance(result, list):
                        result = result[int(key)]
                    else:
                        return {
                            "success": False,
                            "error": f"Cannot traverse into {type(result).__name__}"
                        }
            else:
                result = parsed

            return {
                "success": True,
                "path": path or "(root)",
                "result": result,
                "type": type(result).__name__
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
                "available_tools": list(self.available_tools.keys())
            }

        try:
            tool_func = self.available_tools[tool_name]
            return tool_func(**kwargs)
        except TypeError as e:
            # Wrong arguments
            desc = self.tool_descriptions.get(tool_name, {})
            return {
                "success": False,
                "error": f"Invalid arguments: {e}",
                "expected_params": desc.get("params", {}),
                "example": desc.get("example", "")
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Tool execution failed: {str(e)}"
            }

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
        self,
        name: str,
        func,
        description: str,
        params: dict[str, str],
        example: str
    ):
        """Register a custom tool."""
        self.available_tools[name] = func
        self.tool_descriptions[name] = {
            "description": description,
            "params": params,
            "example": example
        }
