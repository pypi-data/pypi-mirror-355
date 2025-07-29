import json
import logging
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Dict, Optional, Set, Tuple, Union

from ..core import Stats, check_resource_limits
from .base import Engine

logger = logging.getLogger(__name__)


class PythonEngine(Engine):
    """Python execution engine with improved sandboxing and logging"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.modules_dir = Path(tempfile.gettempdir()) / "lam_python_modules"
        self.modules_dir.mkdir(exist_ok=True)
        
        # Define allowed modules - more permissive list
        self.allowed_modules = {
            # Core modules
            "json", "datetime", "math", "statistics", "collections", 
            "itertools", "functools", "re", "copy", "decimal",
            "csv", "io", "dataclasses", "typing", "enum",
            # Additional useful modules
            "time", "random", "uuid", "hashlib", "base64",
            "urllib", "urllib.parse", "html", "xml", "xml.etree",
            "xml.etree.ElementTree", "string", "textwrap",
            "operator", "bisect", "heapq", "array",
            "unicodedata", "locale", "calendar", "zoneinfo",
            # Data processing
            "struct", "binascii", "codecs", "difflib",
            "pprint", "reprlib", "abc", "contextlib",
            "secrets", "fractions", "numbers"
        }
        
        # Dangerous modules that are always blocked
        self.blocked_modules = {
            "subprocess", "os", "sys", "shutil", "pathlib",
            "socket", "pickle", "multiprocessing", "threading",
            "importlib", "builtins", "_thread", "ctypes",
            "marshal", "code", "codeop", "ast", "compile",
            "__builtin__", "__main__", "gc", "inspect",
            "asyncio", "concurrent", "signal", "select",
            "mmap", "sqlite3", "dbm", "shelve",
            "tempfile", "glob", "fnmatch", "fileinput",
            "zipfile", "tarfile", "gzip", "bz2", "lzma",
            "webbrowser", "cgi", "cgitb", "wsgiref",
            "http", "ftplib", "poplib", "imaplib", "smtplib",
            "telnetlib", "uuid", "socketserver", "xmlrpc",
            "ipaddress", "platform", "errno", "pwd", "grp",
            "resource", "pty", "termios", "tty", "fcntl",
            "pipes", "syslog", "ssl", "email"
        }
        
    def validate_environment(self) -> bool:
        logger.debug("Validating Python environment")
        return sys.executable is not None
        
    def check_for_dangerous_code(self, code: str) -> Optional[str]:
        """Check for potentially dangerous patterns in the code"""
        dangerous_patterns = [
            (r"__import__\s*\(", "Use of __import__ is not allowed. Use regular import statements instead."),
            (r"eval\s*\(", "Use of eval() is not allowed for security reasons."),
            (r"exec\s*\(", "Use of exec() is not allowed for security reasons."),
            (r"compile\s*\(", "Use of compile() is not allowed for security reasons."),
            (r"open\s*\(", "Use of open() is not allowed. File system access is restricted."),
            (r"__subclasses__", "Access to __subclasses__ is not allowed for security reasons."),
            (r"__bases__", "Access to __bases__ is not allowed for security reasons."),
            (r"__code__", "Access to __code__ is not allowed for security reasons."),
            (r"__class__\s*\.\s*__", "Access to class internals is restricted."),
            (r"globals\s*\(\s*\)", "Access to globals() is not allowed."),
            (r"locals\s*\(\s*\)", "Access to locals() is not allowed."),
            (r"vars\s*\(\s*\)", "Access to vars() is not allowed."),
            (r"getattr\s*\([^,]+,[^,]+\)", None),  # We'll check this more carefully
            (r"setattr\s*\(", "Use of setattr() is not allowed."),
            (r"delattr\s*\(", "Use of delattr() is not allowed."),
            (r"__dict__", "Direct access to __dict__ is not allowed."),
            (r"__module__", "Access to __module__ is not allowed."),
        ]
        
        for pattern, message in dangerous_patterns:
            if re.search(pattern, code):
                # Special case for getattr - allow for normal attribute access
                if "getattr" in pattern:
                    # Check if it's trying to access dunder methods
                    getattr_matches = re.findall(r"getattr\s*\([^,]+,\s*['\"](__[^'\"]+__)['\"]", code)
                    if getattr_matches:
                        return f"Use of getattr() to access special methods ({getattr_matches[0]}) is not allowed."
                    continue
                
                if message:
                    return message
        
        # Check for imports
        import_pattern = r"(?:^|\n)\s*(?:import|from)\s+(\S+)"
        for match in re.finditer(import_pattern, code, re.MULTILINE):
            module = match.group(1).split('.')[0]  # Get base module
            
            if module in self.blocked_modules:
                return f"Import of '{module}' is not allowed for security reasons."
            
            # Check if it's trying to import something not in allowed list
            if module not in self.allowed_modules and not module.startswith('_'):
                # Give a helpful message about what is allowed
                return (f"Import of '{module}' is not allowed. "
                       f"Available modules include: {', '.join(sorted(list(self.allowed_modules)[:10]))}... "
                       f"(and {len(self.allowed_modules)-10} more)")
        
        return None

    def create_wrapper(self, input_data: str, user_script: str) -> str:
        """Create the wrapper script with enhanced logging and debugging"""
        # Perform safety checks before creating wrapper
        safety_issue = self.check_for_dangerous_code(user_script)
        if safety_issue:
            # Return a wrapper that will immediately exit with the safety error
            return f'''
import json
import sys

sys.stderr.write(json.dumps({{
    "error": "Security violation: {safety_issue}",
    "type": "SecurityError",
    "stack": ["Security check failed", "{safety_issue}"]
}}))
sys.exit(1)
'''

        return f'''
import json
import sys
import traceback
import io
import contextlib
from datetime import datetime
import time

# Import all allowed modules
import re
import math
import statistics
import collections
import itertools
import functools
import copy
import decimal
import csv
import dataclasses
import typing
import enum
import random
import uuid
import hashlib
import base64
import urllib
import urllib.parse
import html
import xml
import xml.etree.ElementTree
import string
import textwrap
import operator
import bisect
import heapq
import array
import unicodedata
import locale
import calendar
import struct
import binascii
import codecs
import difflib
import pprint
import reprlib
import abc
import contextlib as contextlib_module
import secrets
import fractions
import numbers

# Try to import zoneinfo (Python 3.9+)
try:
    import zoneinfo
except ImportError:
    zoneinfo = None

# Resource limiting
try:
    import resource
    import signal
    HAS_RESOURCE_LIMITS = True
except ImportError:
    HAS_RESOURCE_LIMITS = False

# Enhanced logging system
class LogCapture:
    def __init__(self):
        self.logs = []
        self.buffer = []
        
    def write(self, message):
        if message.strip():
            self.logs.append({{
                "type": "log",
                "message": message.strip(),
                "timestamp": time.time()
            }})
        return len(message)
        
    def flush(self):
        pass

class ErrorCapture:
    def __init__(self):
        self.logs = []
        
    def write(self, message):
        if message.strip():
            self.logs.append({{
                "type": "error", 
                "message": message.strip(),
                "timestamp": time.time()
            }})
        return len(message)
        
    def flush(self):
        pass

# Create log captures
stdout_capture = LogCapture()
stderr_capture = ErrorCapture()

# Enhanced console object for better logging
class Console:
    def __init__(self, stdout, stderr):
        self.stdout = stdout
        self.stderr = stderr
        
    def log(self, *args, **kwargs):
        message = ' '.join(str(arg) for arg in args)
        self.stdout.write(message + '\\n')
        
    def error(self, *args, **kwargs):
        message = ' '.join(str(arg) for arg in args)
        self.stderr.write(message + '\\n')
        
    def warn(self, *args, **kwargs):
        message = ' '.join(str(arg) for arg in args)
        self.stderr.write(f"WARNING: {{message}}\\n")
        
    def info(self, *args, **kwargs):
        self.log(*args, **kwargs)
        
    def debug(self, *args, **kwargs):
        message = ' '.join(str(arg) for arg in args)
        self.stdout.write(f"DEBUG: {{message}}\\n")
        
    def table(self, data):
        # Simple table formatting
        if isinstance(data, dict):
            for k, v in data.items():
                self.log(f"{{k}}: {{v}}")
        elif isinstance(data, list):
            for item in data:
                self.log(str(item))
        else:
            self.log(str(data))

console = Console(stdout_capture, stderr_capture)

# Set resource limits if available
if HAS_RESOURCE_LIMITS:
    def set_resource_limits():
        # 10 seconds CPU time (more generous)
        resource.setrlimit(resource.RLIMIT_CPU, (10, 10))
        
        # 200MB memory limit
        memory_limit = 200 * 1024 * 1024  # 200MB in bytes
        resource.setrlimit(resource.RLIMIT_AS, (memory_limit, memory_limit))
        
        # Set timeout handler
        def timeout_handler(signum, frame):
            error_info = {{
                "error": "Execution timed out (10 seconds)",
                "type": "TimeoutError",
                "stack": ["Timeout handler triggered", "Maximum execution time exceeded"]
            }}
            sys.stderr.write(json.dumps(error_info))
            sys.exit(1)
        
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(10)  # 10 second timeout

    try:
        set_resource_limits()
    except Exception as e:
        # Continue if resource limiting fails (e.g., on Windows)
        pass

# Capture stdout and stderr
original_stdout = sys.stdout
original_stderr = sys.stderr
sys.stdout = stdout_capture
sys.stderr = stderr_capture

# Enhanced print function that goes to our logging
def print(*args, sep=' ', end='\\n', file=None, flush=False):
    output = sep.join(str(arg) for arg in args) + end
    if file is sys.stderr:
        stderr_capture.write(output)
    else:
        stdout_capture.write(output)

# Parse input data
input_data = None
try:
    input_data_raw = r"""{input_data}"""
    input_data = json.loads(input_data_raw)
except json.JSONDecodeError as e:
    error_info = {{
        "error": f"Failed to parse input data: {{e}}",
        "type": "JSONDecodeError",
        "stack": []
    }}
    original_stderr.write(json.dumps(error_info))
    sys.exit(1)

# Custom import hook for better error messages
class RestrictedImporter:
    def __init__(self, allowed_modules, blocked_modules):
        self.allowed_modules = allowed_modules
        self.blocked_modules = blocked_modules
        
    def __call__(self, name, globals=None, locals=None, fromlist=(), level=0):
        base_module = name.split('.')[0]
        
        if base_module in self.blocked_modules:
            raise ImportError(
                f"Import of '{{name}}' is blocked for security reasons. "
                f"This module can access system resources that are not allowed in the sandbox."
            )
        
        if base_module not in self.allowed_modules and not base_module.startswith('_'):
            available = sorted(list(self.allowed_modules))[:15]
            raise ImportError(
                f"Import of '{{name}}' is not in the allowed module list. "
                f"Available modules include: {{', '.join(available)}}... "
                f"({{len(self.allowed_modules)}} total modules available)"
            )
            
        return __import__(name, globals, locals, fromlist, level)

# Create restricted builtins
restricted_builtins = {{
    # Safe built-in functions
    "abs": abs, "all": all, "any": any, "ascii": ascii,
    "bin": bin, "bool": bool, "bytearray": bytearray, "bytes": bytes,
    "callable": callable, "chr": chr, "classmethod": classmethod,
    "complex": complex, "dict": dict, "dir": dir, "divmod": divmod,
    "enumerate": enumerate, "filter": filter, "float": float,
    "format": format, "frozenset": frozenset, "getattr": getattr,
    "hasattr": hasattr, "hash": hash, "hex": hex, "id": id,
    "int": int, "isinstance": isinstance, "issubclass": issubclass,
    "iter": iter, "len": len, "list": list, "map": map,
    "max": max, "memoryview": memoryview, "min": min, "next": next,
    "object": object, "oct": oct, "ord": ord, "pow": pow,
    "print": print, "property": property, "range": range,
    "repr": repr, "reversed": reversed, "round": round,
    "set": set, "slice": slice, "sorted": sorted,
    "staticmethod": staticmethod, "str": str, "sum": sum,
    "super": super, "tuple": tuple, "type": type, "zip": zip,
    
    # Exception types
    "BaseException": BaseException, "Exception": Exception,
    "ArithmeticError": ArithmeticError, "AssertionError": AssertionError,
    "AttributeError": AttributeError, "EOFError": EOFError,
    "ImportError": ImportError, "IndexError": IndexError,
    "KeyError": KeyError, "KeyboardInterrupt": KeyboardInterrupt,
    "LookupError": LookupError, "MemoryError": MemoryError,
    "NameError": NameError, "NotImplementedError": NotImplementedError,
    "OSError": OSError, "OverflowError": OverflowError,
    "RecursionError": RecursionError, "ReferenceError": ReferenceError,
    "RuntimeError": RuntimeError, "StopIteration": StopIteration,
    "SyntaxError": SyntaxError, "SystemError": SystemError,
    "TypeError": TypeError, "UnboundLocalError": UnboundLocalError,
    "UnicodeError": UnicodeError, "ValueError": ValueError,
    "ZeroDivisionError": ZeroDivisionError,
    
    # Restricted import function
    "__import__": RestrictedImporter(
        {json.dumps(list(self.allowed_modules))},
        {json.dumps(list(self.blocked_modules))}
    ),
    
    # Constants
    "True": True, "False": False, "None": None,
    "NotImplemented": NotImplemented, "Ellipsis": Ellipsis,
}}

# Create safe globals with pre-imported modules
safe_globals = {{
    "__builtins__": restricted_builtins,
    "console": console,
    
    # Pre-imported safe modules
    "json": json, "datetime": datetime, "time": time,
    "math": math, "statistics": statistics,
    "collections": collections, "itertools": itertools,
    "functools": functools, "re": re, "copy": copy,
    "decimal": decimal, "csv": csv, "io": io,
    "dataclasses": dataclasses, "typing": typing,
    "enum": enum, "random": random, "uuid": uuid,
    "hashlib": hashlib, "base64": base64,
    "urllib": urllib, "html": html, "xml": xml,
    "string": string, "textwrap": textwrap,
    "operator": operator, "bisect": bisect,
    "heapq": heapq, "array": array,
    "unicodedata": unicodedata, "locale": locale,
    "calendar": calendar, "struct": struct,
    "binascii": binascii, "codecs": codecs,
    "difflib": difflib, "pprint": pprint,
    "reprlib": reprlib, "abc": abc,
    "contextlib": contextlib_module,
    "secrets": secrets, "fractions": fractions,
    "numbers": numbers,
}}

if zoneinfo:
    safe_globals["zoneinfo"] = zoneinfo

# Create safe locals with input data
safe_locals = {{"input_data": input_data}}

# Helper function for better error formatting
def format_error_context(exc_type, exc_value, exc_tb):
    """Extract detailed context about an error"""
    error_msg = str(exc_value)
    
    # Special handling for KeyError to provide more context
    if exc_type.__name__ == 'KeyError':
        # The key that wasn't found
        missing_key = str(exc_value).strip("'")
        
        # Try to get the code that caused the error
        tb_frames = list(traceback.extract_tb(exc_tb))
        if tb_frames:
            last_frame = tb_frames[-1]
            code_line = last_frame.line
            
            if code_line:
                # Look for dictionary access patterns to provide context
                import re
                
                # Check if it's a nested access - use simpler pattern
                if f"['{{missing_key}}']" in code_line:
                    # Extract the object being accessed
                    match = re.search(r'(\w+(?:\[[^\]]+\])*)\[[^\]]+\]', code_line)
                    if match:
                        accessed_obj = match.group(1)
                        error_msg = f"KeyError: '{{missing_key}}' not found in {{accessed_obj}}"
                    else:
                        error_msg = f"KeyError: dictionary key '{{missing_key}}' not found"
                else:
                    error_msg = f"KeyError: dictionary key '{{missing_key}}' not found"
    
    elif exc_type.__name__ == 'AttributeError':
        # Try to extract what object and attribute were involved
        import re
        match = re.search(r"'(\w+)' object has no attribute '(\w+)'", error_msg)
        if match:
            obj_type, attr = match.groups()
            error_msg = f"AttributeError: '{{obj_type}}' object has no attribute '{{attr}}'"
    
    elif exc_type.__name__ == 'IndexError':
        # Enhance index errors
        if "list index out of range" in error_msg:
            tb_frames = list(traceback.extract_tb(exc_tb))
            if tb_frames:
                last_frame = tb_frames[-1]
                code_line = last_frame.line
                if code_line and '[' in code_line:
                    # Try to extract what list was being accessed
                    match = re.search(r"(\w+)\[", code_line)
                    if match:
                        list_name = match.group(1)
                        error_msg = f"IndexError: list index out of range when accessing {{list_name}}"
    
    elif exc_type.__name__ == 'TypeError':
        # Keep TypeError messages as they usually have good context
        pass
    
    return error_msg

# Execute user script
transform_fn = None
execution_start = time.time()

try:
    # Compile the user script
    compiled_code = compile(r"""{user_script}""", "<user_script>", "exec")
    
    # Execute in restricted environment
    exec(compiled_code, safe_globals, safe_locals)
    
    # Validate transform function
    if 'transform' not in safe_locals:
        raise NameError(
            "No 'transform' function defined. Your script must define a function "
            "named 'transform' that takes the input data as its parameter."
        )
    
    transform_fn = safe_locals['transform']
    
    if not callable(transform_fn):
        raise TypeError(
            f"'transform' must be a function, but got {{type(transform_fn).__name__}}. "
            "Make sure you define it as: def transform(data): ..."
        )
    
    # Check function signature (basic check)
    import inspect
    try:
        sig = inspect.signature(transform_fn)
        param_count = len(sig.parameters)
        if param_count != 1:
            raise TypeError(
                f"'transform' function must accept exactly 1 parameter, "
                f"but it accepts {{param_count}}. "
                f"Define it as: def transform(data): ..."
            )
    except Exception:
        # If signature inspection fails, continue anyway
        pass
    
except SyntaxError as e:
    # Enhanced syntax error reporting
    error_info = {{
        "error": f"SyntaxError: {{e.msg}}",
        "type": "SyntaxError",
        "stack": [],
        "traceback": [{{
            "file": "user_script.py",
            "line": e.lineno,
            "function": "<module>",
            "code": e.text.strip() if e.text else ""
        }}]
    }}
    original_stderr.write(json.dumps(error_info))
    sys.exit(1)
    
except Exception as e:
    # Extract detailed traceback information
    import traceback as tb_module
    tb_info = []
    
    # Get the traceback
    exc_type, exc_value, exc_tb = sys.exc_info()
    
    # Format traceback with more details
    for frame in tb_module.extract_tb(exc_tb):
        if '<user_script>' in frame.filename or '<string>' in frame.filename:
            tb_info.append({{
                "file": "user_script.py",
                "line": frame.lineno,
                "function": frame.name,
                "code": frame.line.strip() if frame.line else ""
            }})
    
    error_info = {{
        "error": str(e),
        "type": type(e).__name__,
        "traceback": tb_info,
        "stack": []
    }}
    
    original_stderr.write(json.dumps(error_info))
    sys.exit(1)

# Execute transform function
transform_start = time.time()
result = None

try:
    # Cancel alarm if set
    if HAS_RESOURCE_LIMITS:
        signal.alarm(0)
    
    # Call transform with input data
    result = transform_fn(input_data)
    
    # Validate result is JSON serializable
    try:
        json.dumps(result)
    except (TypeError, ValueError) as e:
        # Try to find what's not serializable
        def find_non_serializable(obj, path="result"):
            if isinstance(obj, (str, int, float, bool, type(None))):
                return None
            elif isinstance(obj, dict):
                for k, v in obj.items():
                    issue = find_non_serializable(v, f"{{path}}[{{repr(k)}}]")
                    if issue:
                        return issue
            elif isinstance(obj, (list, tuple)):
                for i, v in enumerate(obj):
                    issue = find_non_serializable(v, f"{{path}}[{{i}}]")
                    if issue:
                        return issue
            else:
                return f"{{path}} contains non-serializable type: {{type(obj).__name__}}"
        
        issue = find_non_serializable(result)
        raise TypeError(
            f"Transform result is not JSON serializable. {{issue or str(e)}}. "
            "Make sure your transform function returns only JSON-compatible types "
            "(dict, list, str, int, float, bool, None)."
        )
    
except Exception as e:
    # Get detailed error information
    import traceback as tb_module
    exc_type, exc_value, exc_tb = sys.exc_info()
    
    # Get the original exception if this is a wrapped exception
    original_error = str(e)
    error_context = ""
    
    # If this is a wrapped ValueError, try to get the original error
    if isinstance(e, ValueError) and "Failed to process:" in str(e):
        # Use exception chaining to get the cause
        if hasattr(e, '__context__') and e.__context__:
            # Get the original exception that was caught
            orig_exc = e.__context__
            orig_type = type(orig_exc).__name__
            
            # Format the original error with context
            enhanced_msg = format_error_context(type(orig_exc), orig_exc, orig_exc.__traceback__)
            original_error = f"Failed to process: {{enhanced_msg}}"
    
    # Build traceback info focusing on user code
    tb_info = []
    for frame in tb_module.extract_tb(exc_tb):
        if '<user_script>' in frame.filename or '<string>' in frame.filename or 'transform' in frame.name:
            tb_info.append({{
                "file": "user_script.py",
                "line": frame.lineno,
                "function": frame.name,
                "code": frame.line.strip() if frame.line else ""
            }})
    
    stack_trace = []
    
    # First line: Error type and message (like JS)
    stack_trace.append(f"{{type(e).__name__}}: {{original_error}}")
    
    # Add traceback entries
    for tb_entry in tb_info:
        stack_trace.append(f"    at {{tb_entry['function']}} ({{tb_entry['file']}}:{{tb_entry['line']}})")
    
    error_info = {{
        "error": original_error,
        "type": type(e).__name__,
        "traceback": tb_info,
        "stack": stack_trace
    }}
    
    original_stderr.write(json.dumps(error_info))
    sys.exit(1)

before_write = {{
    "result": result,
    "logs": stdout_capture.logs + stderr_capture.logs
}}

stdout_capture.write(f"Writing output: {{json.dumps(before_write, indent=2)}}")

# Prepare final output
output = {{
    "result": result,
    "logs": stdout_capture.logs + stderr_capture.logs
}}

# Write successful result
original_stdout.write(json.dumps(output))
'''

    def execute(self, program_file: str, input_data: str) -> Tuple[Union[Dict, str], Optional[str]]:
        logger.info(f"Executing Python script: {program_file}")
        stats = Stats()

        try:
            check_resource_limits(self.modules_dir)

            with tempfile.TemporaryDirectory() as temp_dir:
                temp_dir = Path(temp_dir)
                
                # Read user script
                with open(program_file, 'r') as f:
                    user_script = f.read()
                    logger.debug("Loaded user Python script: %d characters", len(user_script))
                
                # Check for dangerous code
                safety_issue = self.check_for_dangerous_code(user_script)
                if safety_issue:
                    logger.warning(f"Security violation detected in script: {safety_issue}")
                    return {
                        "lam.error": f"Security violation: {safety_issue}",
                        "type": "SecurityError"
                    }, f"Security violation: {safety_issue}"

                # Create wrapper script with enhanced error handling
                wrapper = self.create_wrapper(input_data, user_script)
                script_path = temp_dir / "script.py"
                with open(script_path, 'w') as f:
                    f.write(wrapper)
                logger.debug("Generated Python wrapper script: %s", script_path)

                # Execute with Python in isolated environment
                process = subprocess.Popen(
                    [
                        sys.executable,
                        "-I",  # Isolated mode
                        str(script_path)
                    ],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    cwd=temp_dir,
                    env={"PATH": os.environ.get("PATH", "")}
                )
                logger.info("Started Python process PID %d", process.pid)

                try:
                    output, error = process.communicate(timeout=10)
                    logger.debug("Process completed with code %d", process.returncode)
                except subprocess.TimeoutExpired:
                    logger.warning("Process timeout after 10 seconds")
                    process.kill()
                    return {
                        "lam.error": "Script execution timed out",
                        "type": "TimeoutError"
                    }, "Execution timed out after 10 seconds"

                # Handle process errors with enhanced logging
                if process.returncode != 0:
                    try:
                        # Try to parse structured error from stderr
                        error_data = json.loads(error.strip())
                        error_msg = error_data.get('error', 'Unknown error')
                        error_type = error_data.get('type', 'Error')
                        
                        # Format error response similar to JS engine
                        error_details = {
                            "lam.error": error_msg,
                        }
                        
                        # Use the pre-formatted stack trace if available
                        if 'stack' in error_data and error_data['stack']:
                            error_details["stack_trace"] = error_data['stack']
                        else:
                            # Fallback: format stack trace similar to JS
                            stack_lines = []
                            
                            # Add main error line
                            stack_lines.append(f"{error_type}: {error_msg}")
                            
                            # Add traceback entries in JS style
                            if 'traceback' in error_data:
                                for tb in error_data['traceback']:
                                    file = tb.get('file', 'unknown')
                                    line = tb.get('line', 0)
                                    func = tb.get('function', '<module>')
                                    stack_lines.append(f"    at {func} ({file}:{line})")
                            
                            error_details["stack_trace"] = stack_lines
                        
                        # Log the error details
                        logger.error("Python execution error: %s (%s)", error_msg, error_type)
                        if 'traceback' in error_data:
                            for tb_entry in error_data['traceback']:
                                logger.error("  at %s:%d in %s()", 
                                           tb_entry.get('file', 'unknown'),
                                           tb_entry.get('line', 0),
                                           tb_entry.get('function', 'unknown'))
                        
                        return error_details, error_msg
                        
                    except json.JSONDecodeError:
                        # Fallback to raw error output
                        error_msg = error.strip() or "Unknown error"
                        logger.error("Failed to parse error JSON, raw error: %s", error_msg)
                        return {"lam.error": error_msg}, error_msg

                # Handle successful output
                try:
                    output_data = json.loads(output)
                    
                    # Process Python logs
                    if 'logs' in output_data:
                        for log_entry in output_data.get('logs', []):
                            log_type = log_entry.get('type', 'log')
                            message = log_entry.get('message', '')
                            
                            # Log "Writing result:" message like JS engine
                            if message.startswith('Writing result:'):
                                logger.debug("[Python] %s", message)
                            elif log_type == 'error':
                                logger.error("[Python] %s", message)
                            elif 'WARNING:' in message:
                                logger.warning("[Python] %s", message)
                            elif 'DEBUG:' in message:
                                logger.debug("[Python] %s", message)
                            else:
                                logger.info("[Python] %s", message)
                    
                    result = output_data.get('result', {})
                    return result, None

                except json.JSONDecodeError as e:
                    logger.error("Failed to parse output as JSON: %s", str(e))
                    logger.error("Raw output: %s", output[:500])  # Log first 500 chars
                    return {
                        "lam.error": "Invalid JSON output from transform",
                        "parse_error": str(e),
                        "raw_output": output.strip()[:1000]  # Include some of the output
                    }, "Output format error"

        except Exception as e:
            logger.exception("Python engine execution failed")
            return {
                "lam.error": str(e),
                "type": e.__class__.__name__
            }, str(e)