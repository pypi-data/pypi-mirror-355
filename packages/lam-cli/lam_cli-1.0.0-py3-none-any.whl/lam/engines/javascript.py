import json
import logging
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Dict, Optional, Tuple, Union

from ..core import ProcessingError, Stats, check_resource_limits
from .base import Engine

logger = logging.getLogger(__name__)


class BunEngine(Engine):
    """Bun JavaScript execution engine with enhanced logging"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.modules_dir = Path(tempfile.gettempdir()) / "lam_modules"
        self.modules_dir.mkdir(exist_ok=True)
        self._setup_shared_modules()
        
        self.runtime_template = '''
        const logs = [];
        const originalLog = console.log;
        const originalError = console.error;
        const originalWarn = console.warn;
        
        console.log = (...args) => logs.push({ type: 'log', message: args.map(String).join(' ') });
        console.error = (...args) => {
            originalError(...args);  // Keep error output for debugging
            logs.push({ type: 'error', message: args.map(String).join(' ') });
        };
        console.warn = (...args) => logs.push({ type: 'warn', message: args.map(String).join(' ') });
        
        // Keep original stdout for result output
        const writeResult = (obj) => {
            console.log("Writing result:", JSON.stringify(obj, null, 2));
            originalLog(JSON.stringify(obj));
        };
        
        const _ = require('lodash');
        const { format, parseISO } = require('date-fns');
        
        module.exports = {
            _,
            format,
            parseISO,
            logs,
            writeResult
        };
        '''

    def _setup_shared_modules(self):
        """Setup shared node_modules once"""
        if not (self.modules_dir / "node_modules").exists():
            logger.info("Initializing shared modules directory")
            package_json = {
                "dependencies": {
                    "lodash": "^4.17.21",
                    "date-fns": "^2.30.0"
                }
            }
            with open(self.modules_dir / "package.json", "w") as f:
                json.dump(package_json, f, indent=2)

            try:
                logger.debug("Installing shared dependencies")
                result = subprocess.run(
                    [self.get_bun_path(), "install"],
                    cwd=self.modules_dir,
                    check=True,
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                logger.debug("Dependency install output: %s", result.stdout)
            except subprocess.CalledProcessError as e:
                logger.error("Dependency install failed: %s", e.stderr)
                raise ProcessingError(f"Environment setup failed: {e.stderr}") from e

    def create_wrapper(self, input_data: str, user_script: str) -> str:
        """Create the wrapper script with proper escaping"""
        return f'''
        const {{ _, format, parseISO, logs, writeResult }} = require('./runtime.js');

        // Utility function to handle circular references in JSON.stringify
        function safeStringify(obj) {{
            const seen = new WeakSet();
            return JSON.stringify(obj, (key, value) => {{
                if (typeof value === 'object' && value !== null) {{
                    if (seen.has(value)) {{
                        return '[Circular Reference]';
                    }}
                    seen.add(value);
                }}
                return value;
            }}, 2);
        }}

        // Validate transform function
        function validateTransform(fn) {{
            if (typeof fn !== 'function') {{
                throw new Error('Transform must be a function');
            }}
            if (fn.length !== 1) {{
                throw new Error('Transform function must accept exactly one argument (input)');
            }}
        }}

        // Execute transform immediately
        try {{
            // Parse input safely
            let input;
            try {{
                input = JSON.parse({json.dumps(input_data)});
            }} catch (e) {{
                throw new Error(`Failed to parse input data: ${{e.message}}`);
            }}

            // Get transform function
            let transform;
            try {{
                transform = {user_script};
            }} catch (e) {{
                throw new Error(`Failed to parse transform function: ${{e.message}}`);
            }}

            // Validate transform
            validateTransform(transform);

            // Execute transform
            const result = transform(input);

            // Output result after transform
            writeResult({{
                result,
                logs
            }});
        }} catch (error) {{
            console.error(JSON.stringify({{
                error: error.message,
                stack: error.stack?.split('\\n') || [],
                type: error.constructor.name
            }}));
            process.exit(1);
        }}
        '''
    
    def setup_environment(self, temp_dir: Path) -> None:
        """Set up the JavaScript environment with runtime"""
        # Write runtime file only
        runtime_path = temp_dir / "runtime.js"
        with open(runtime_path, "w") as f:
            f.write(self.runtime_template)
        logger.debug("Runtime file written to: %s", runtime_path)
        
        # Symlink node_modules from shared directory
        os.symlink(self.modules_dir / "node_modules", temp_dir / "node_modules")
        logger.debug("node_modules symlinked from: %s", self.modules_dir / "node_modules")

    def validate_environment(self) -> bool:
        # Check multiple locations for bun
        possible_locations = [
            "bun",  # System PATH
            os.path.join(os.path.dirname(sys.executable), "bun"),  # venv/bin
            os.path.join(os.path.dirname(os.path.dirname(sys.executable)), "bin", "bun")  # venv/bin (alternative)
        ]
        
        return any(shutil.which(loc) is not None for loc in possible_locations)

    def get_bun_path(self) -> str:
        """Get the appropriate bun executable path"""
        possible_locations = [
            "bun",
            os.path.join(os.path.dirname(sys.executable), "bun"),
            os.path.join(os.path.dirname(os.path.dirname(sys.executable)), "bin", "bun")
        ]
        
        for loc in possible_locations:
            if shutil.which(loc):
                return shutil.which(loc)
        
        raise EnvironmentError("Bun not found in environment")

    def execute(self, program_file: str, input_data: str) -> Tuple[Union[Dict, str], Optional[str]]:
        logger.info(f"Executing Bun script: {program_file}")
        stats = Stats()

        try:
            check_resource_limits(self.modules_dir)

            with tempfile.TemporaryDirectory() as temp_dir:
                temp_dir = Path(temp_dir)
                self.setup_environment(temp_dir)

                # Read user script
                with open(program_file, 'r') as f:
                    user_script = f.read()
                    logger.debug("Loaded user script: %d characters", len(user_script))

                # Create wrapper script
                wrapper = self.create_wrapper(input_data, user_script)
                script_path = temp_dir / "script.js"
                with open(script_path, 'w') as f:
                    f.write(wrapper)
                logger.debug("Generated wrapper script: %s", script_path)

                # Execute with Bun
                process = subprocess.Popen(
                    [
                        self.get_bun_path(),
                        "run",
                        "--no-fetch",
                        "--smol",
                        "--silent",
                        str(script_path)
                    ],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    cwd=temp_dir
                )
                logger.info("Started Bun process PID %d", process.pid)

                try:
                    output, error = process.communicate(timeout=5)
                    logger.debug("Process completed with code %d", process.returncode)
                except subprocess.TimeoutExpired as e:
                    logger.warning("Process timeout after 5 seconds")
                    process.kill()
                    return {"lam.error": "Script execution timed out"}, "Execution timed out after 5 seconds"

                # Handle process errors
                if process.returncode != 0:
                    try:
                        # Try to parse structured error from stderr
                        error_data = json.loads(error.strip())
                        error_msg = error_data.get('error', 'Unknown error')
                        stack = error_data.get('stack', [])
                        
                        # Format error message
                        error_details = {
                            "lam.error": error_msg,
                            "stack_trace": stack
                        }
                        return error_details, error_msg
                        
                    except json.JSONDecodeError:
                        # Fallback to raw error output
                        error_msg = error.strip() or "Unknown error"
                        return {"lam.error": error_msg}, error_msg

                # Handle successful output
                try:
                    output_data = json.loads(output)
                    
                    # Process JavaScript logs (if any)
                    if 'logs' in output_data:
                        for log_entry in output_data.get('logs', []):
                            if log_entry['type'] == 'error':
                                logger.error("[JS] %s", log_entry['message'])
                            else:
                                logger.debug("[JS] %s", log_entry['message'])
                    
                    result = output_data.get('result', {})
                    return result, None

                except json.JSONDecodeError as e:
                    logger.error("Failed to parse output: %s", str(e))
                    return {
                        "lam.error": "Invalid JSON output",
                        "raw_output": output.strip()
                    }, "Output format error"

        except Exception as e:
            logger.exception("Execution failed")
            return {
                "lam.error": str(e),
                "type": e.__class__.__name__
            }, str(e) 