import json
import logging
import shutil
import subprocess
from typing import Dict, Optional, Tuple, Union

from ..core import ProcessingError
from .base import Engine

logger = logging.getLogger(__name__)


class JQEngine(Engine):
    """JQ execution engine"""
    def validate_environment(self) -> bool:
        logger.debug("Validating JQ environment")
        return shutil.which("jq") is not None

    def execute(self, program_file: str, input_data: str) -> Tuple[Union[Dict, str], Optional[str]]:
        logger.info(f"Executing JQ script: {program_file}")
        
        try:
            with open(program_file, 'r') as file:
                jq_script = ''.join(line for line in file if not line.strip().startswith('#'))
                logger.debug("Loaded JQ script: %d characters", len(jq_script))

            process = subprocess.Popen(
                ["jq", "-c", jq_script],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            logger.debug("Starting JQ process PID %d", process.pid)
            output, error = process.communicate(input=input_data)
            
            if error:
                logger.error("JQ error output: %s", error.strip())
                raise ProcessingError(error)
                
            # Handle output
            try:
                output_lines = [line.strip() for line in output.splitlines() if line.strip()]
                logger.debug(f"Found {len(output_lines)} JSON objects in output")
                
                if len(output_lines) > 1:
                    parsed = [json.loads(line) for line in output_lines]
                    logger.info(f"Processed {len(parsed)} JSON objects")
                    return {"lam.result": parsed}, None
                elif len(output_lines) == 1:
                    result = json.loads(output_lines[0])
                    logger.info("Processed single JSON object")
                    return result, None
                else:
                    logger.info("No JSON objects in output")
                    return {"lam.error": "No JSON objects in output"}, "No JSON objects in output"
                    
            except json.JSONDecodeError as e:
                return {"lam.result": output}, None
                
        except Exception as e:
            logger.exception("JQ execution failed")
            self.track_event('lam.jq.error', {'error': str(e)})
            return {"lam.error": str(e)}, str(e) 