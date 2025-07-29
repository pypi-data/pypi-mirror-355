#!/usr/bin/env python3

import logging
import os
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import psutil
from logtail import LogtailHandler


def setup_logging():
    """Configure logging with UTC timezone and handlers"""
    # Configure logging with UTC timezone
    logging.Formatter.converter = lambda *args: datetime.now(timezone.utc).timetuple()
    
    # Set up root logger configuration
    logging.basicConfig(
        level=logging.DEBUG, 
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        force=True  # Override any existing configuration
    )
    
    # Suppress noisy loggers
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    
    # Add LogTail handler to root logger
    root_logger = logging.getLogger()
    handler = LogtailHandler(source_token="TYz3WrrvC8ehYjXdAEGGyiDp")
    root_logger.addHandler(handler)
    
    return logging.getLogger(__name__)


class LAMError(Exception):
    """Base exception for LAM errors"""
    pass


class UserError(LAMError):
    """Errors caused by user input"""
    pass


class SystemError(LAMError):
    """Errors caused by system issues"""
    pass


class ResourceLimitError(LAMError):
    """Errors caused by resource limits"""
    pass


class ProcessingError(Exception):
    """Custom exception for processing errors"""
    pass


def check_resource_limits(modules_dir: Optional[Path] = None) -> None:
    """Check system resource availability"""
    disk = shutil.disk_usage(tempfile.gettempdir())
    if disk.free < 100 * 1024 * 1024:  # 100MB minimum
        raise ResourceLimitError("Insufficient disk space")
    
    if modules_dir and modules_dir.exists():
        modules_size = sum(
            os.path.getsize(os.path.join(dirpath, filename))
            for dirpath, _, filenames in os.walk(modules_dir)
            for filename in filenames
        )
        if modules_size > 500 * 1024 * 1024:
            shutil.rmtree(modules_dir)
            modules_dir.mkdir(exist_ok=True)


class Stats:
    """Track execution statistics"""
    def __init__(self):
        self.start_time = datetime.now()
        self.memory_start = self.get_memory_usage()
    
    def get_memory_usage(self):
        process = psutil.Process()
        return process.memory_info().rss
    
    def finalize(self):
        return {
            'duration_ms': (datetime.now() - self.start_time).total_seconds() * 1000,
            'memory_used_mb': (self.get_memory_usage() - self.memory_start) / (1024 * 1024),
            'timestamp': datetime.now().isoformat()
        } 