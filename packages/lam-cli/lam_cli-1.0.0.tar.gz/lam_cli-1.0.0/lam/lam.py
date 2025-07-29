#!/usr/bin/env python3

import json
import logging

import click

from .core import ProcessingError, Stats, setup_logging
from .engines import get_engine
from .engines.javascript import BunEngine
from .engines.jq import JQEngine
from .engines.python import PythonEngine
from .utils import process_input

# Set up logging once at module level
logger = setup_logging()


@click.group()
def lam():
    """LAM - Laminar Data Transformation Tool"""
    pass


@lam.command()
def initialize():
    """Initialize shared modules for supported engines."""
    click.echo("Starting LAM initialization...")
    
    engine_classes = [BunEngine, PythonEngine, JQEngine]

    # Define placeholder IDs for engine instantiation during initialization
    init_workspace_id = "lam_init_workspace"
    init_flow_id = "lam_init_flow"
    init_execution_id = "lam_init_execution"

    for engine_class in engine_classes:
        engine_name = engine_class.__name__
        click.echo(f"Checking {engine_name} for shared module setup...")
        try:
            # Instantiate engine to access instance methods like _setup_shared_modules
            engine_instance = engine_class(
                workspace_id=init_workspace_id, 
                flow_id=init_flow_id, 
                execution_id=init_execution_id
            )
            
            if hasattr(engine_instance, '_setup_shared_modules') and callable(getattr(engine_instance, '_setup_shared_modules')):
                click.echo(f"Running _setup_shared_modules for {engine_name}...")
                getattr(engine_instance, '_setup_shared_modules')()
                click.echo(f"Successfully initialized shared modules for {engine_name}.")
            else:
                click.echo(f"{engine_name} does not have a _setup_shared_modules method or it's not callable.")
        except Exception as e:
            click.echo(f"Error during initialization of {engine_name}: {e}", err=True)
            logger.error(f"Initialization error for {engine_name}", exc_info=True)

    click.echo("LAM initialization complete.")


@lam.command()
@click.argument('program_file', type=click.Path(exists=True))
@click.argument('input', type=str)
@click.option('--language', type=click.Choice(['jq', 'js', 'py']), default='jq',
              help='Script language (default: jq)')
@click.option('--workspace_id', default="local", help="Workspace ID")
@click.option('--flow_id', default="local", help="Flow ID")
@click.option('--execution_id', default="local", help="Execution ID")
@click.option('--as-json', is_flag=True, default=True, help="Output as JSON")
def run(program_file: str, input: str, language: str, workspace_id: str, 
        flow_id: str, execution_id: str, as_json: bool):
    """Execute a LAM transformation script"""
    stats = Stats()
    
    try:
        engine = get_engine(language, workspace_id, flow_id, execution_id)
    except (ValueError, EnvironmentError) as e:
        click.echo({"lam.error": str(e)}, err=True)
        return

    log_file = engine.get_log_file()
    result_file = engine.get_result_file()
    
    # Add file handler to root logger so ALL loggers write to the file
    file_handler = logging.FileHandler(log_file, 'w')
    file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    root_logger = logging.getLogger()
    root_logger.addHandler(file_handler)
    
    logger.info("Starting LAM execution with %s engine", language)
    engine.track_event('lam.run.start', {
        'language': language,
        'program_file': program_file
    })

    try:
        input_data, error = process_input(input)
        if error:
            raise ProcessingError(f"Invalid input: {error}")

        result, error = engine.execute(program_file, input_data)
        
        stats_data = stats.finalize()
        logger.info("Execution stats: duration=%.2fms, memory=%.2fMB",
                   stats_data['duration_ms'], stats_data['memory_used_mb'])
        
        if error:
            click.echo({"lam.error": error}, err=True)
            engine.track_event('lam.run.error', {'error': error, **stats_data})
        else:
            output = json.dumps(result, indent=4) if as_json else result
            click.echo(output)
            engine.track_event('lam.run.success', stats_data)
            
        if isinstance(result, list):
            result = {"lam.result": result}
        
        with open(result_file, 'w') as f:
            json.dump(result, f, indent=4)
            
    except Exception as e:
        stats_data = stats.finalize()
        logger.error("Execution failed: %s", str(e))
        logger.error("Final stats: duration=%.2fms, memory=%.2fMB",
                    stats_data['duration_ms'], stats_data['memory_used_mb'])
        click.echo({"lam.error": str(e)}, err=True)
        engine.track_event('lam.run.error', {'error': str(e), **stats_data})
        
    finally:
        logger.info("Execution complete")
        root_logger.removeHandler(file_handler)


if __name__ == '__main__':
    lam()