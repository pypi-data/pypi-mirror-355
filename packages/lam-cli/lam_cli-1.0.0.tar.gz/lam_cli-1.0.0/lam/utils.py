import json
import logging
import os
from typing import Optional, Tuple

logger = logging.getLogger(__name__)


def process_input(input: str) -> Tuple[str, Optional[str]]:
    """Process and validate input data"""
    if os.path.isfile(input):
        logger.debug("Loading input from file: %s", input)
        with open(input, 'r') as file:
            return file.read(), None
            
    try:
        json.loads(input)
        logger.debug("Validated inline JSON input")
        return input, None
    except json.JSONDecodeError as e:
        logger.error("Invalid JSON input: %s", str(e))
        return str(e), None