from .base import Engine, EngineType
from .javascript import BunEngine
from .jq import JQEngine
from .python import PythonEngine


def get_engine(engine_type: str, workspace_id: str, flow_id: str, execution_id: str) -> Engine:
    """Factory function to get the appropriate execution engine"""
    engines = {
        EngineType.JQ.value: JQEngine,
        EngineType.JAVASCRIPT.value: BunEngine,
        EngineType.PYTHON.value: PythonEngine
    }
    
    engine_class = engines.get(engine_type)
    if not engine_class:
        raise ValueError(f"Unsupported engine type: {engine_type}")
    
    engine = engine_class(workspace_id, flow_id, execution_id)
    if not engine.validate_environment():
        raise EnvironmentError(f"Required dependencies not found for {engine_type}")
    
    return engine 