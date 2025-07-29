import logging
import os
import socket
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional, Tuple, Union

from posthog import Posthog

# Initialize analytics
posthog = Posthog(project_api_key='phc_wfeHFG0p5yZIdBpjVYy00o5x1HbEpggdMzIuFYgNPSK', 
                  host='https://app.posthog.com')

logger = logging.getLogger(__name__)


class EngineType(Enum):
    JQ = "jq"
    JAVASCRIPT = "js"
    PYTHON = "py"


class Engine:
    """Base class for execution engines"""
    def __init__(self, workspace_id: str, flow_id: str, execution_id: str):
        self.workspace_id = workspace_id
        self.flow_id = flow_id
        self.execution_id = execution_id
        self.timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    def get_log_file(self) -> str:
        return f"lam_run_{self.workspace_id}_{self.flow_id}_{self.execution_id}_{self.timestamp}.log"

    def get_result_file(self) -> str:
        return f"lam_result_{self.workspace_id}_{self.flow_id}_{self.execution_id}_{self.timestamp}.json"

    def track_event(self, event_name: str, properties: Dict[str, Any]) -> None:
        """Track events with PostHog"""
        try:
            distinct_id = f"{os.getuid()}_{socket.gethostname()}_{self.workspace_id}_{self.flow_id}"
            properties |= {
                'workspace_id': self.workspace_id,
                'flow_id': self.flow_id,
                'engine': self.__class__.__name__,
            }
            posthog.capture(distinct_id=distinct_id, event=event_name, properties=properties)
        except Exception as e:
            logger.error(f"Error tracking event: {e}")

    def validate_environment(self) -> bool:
        """Validate that the engine can run in this environment"""
        raise NotImplementedError

    def execute(self, program_file: str, input_data: str) -> Tuple[Union[Dict, str], Optional[str]]:
        """Execute the program with input data"""
        raise NotImplementedError 