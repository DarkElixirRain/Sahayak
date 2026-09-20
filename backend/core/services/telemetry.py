"""
Simplified Telemetry Service - No-op implementation when telemetry is disabled.

This module provides stub implementations that do nothing, replacing the full
OpenTelemetry-based implementation to avoid dependencies.
"""

import functools
import hashlib
import json
import logging
import os
import uuid
from contextlib import nullcontext
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, TypeVar

from core.config import get_settings

# Get settings from config
settings = get_settings()

# Telemetry configuration
TELEMETRY_ENABLED = settings.TELEMETRY_ENABLED
SERVICE_NAME = settings.SERVICE_NAME
METADATA_MAX_LENGTH = 256

logger = logging.getLogger(__name__)


def get_installation_id() -> str:
    """Generate or retrieve a unique anonymous installation ID."""
    id_file = Path.home() / ".databridge" / "installation_id"
    id_file.parent.mkdir(parents=True, exist_ok=True)

    if id_file.exists():
        return id_file.read_text().strip()

    # Generate a new installation ID
    machine_id_file = Path("/etc/machine-id")
    if machine_id_file.exists():
        machine_id = machine_id_file.read_text().strip()
    else:
        machine_id = str(uuid.uuid4())

    installation_id = hashlib.sha256(machine_id.encode()).hexdigest()[:16]
    id_file.write_text(installation_id)
    return installation_id


def sanitize_metadata(metadata: Dict[str, Any]) -> Dict[str, Any]:
    """Simple metadata sanitization (no-op when telemetry disabled)."""
    if not TELEMETRY_ENABLED:
        return {}
    return {k: str(v)[:METADATA_MAX_LENGTH] if isinstance(v, str) else v 
            for k, v in metadata.items() if v is not None}


class TelemetryService:
    """No-op telemetry service when OpenTelemetry is disabled."""
    
    def __init__(self):
        self._enabled = TELEMETRY_ENABLED
        self._installation_id = get_installation_id()
        if self._enabled:
            logger.info("Telemetry initialized (no-op mode)")
        
    def track(
        self,
        operation_type: str,
        metadata_resolver: Optional[Callable] = None,
    ):
        """No-op decorator for tracking operations."""
        def decorator(func):
            @functools.wraps(func)
            async def wrapper(*args, **kwargs):
                # Simply call the original function without tracking
                return await func(*args, **kwargs)
            return wrapper
        return decorator
    
    def track_operation(self, operation_type: str, **kwargs):
        """No-op context manager for tracking operations. Accepts any keyword arguments."""
        return nullcontext()
    
    # Metadata resolver methods - all return empty dicts
    def query_metadata(self, auth_context: Any, request: Any = None) -> Dict[str, Any]:
        """No-op metadata extraction."""
        return {}
    
    def document_pages_metadata(self, auth_context: Any, request: Any = None) -> Dict[str, Any]:
        """No-op metadata extraction."""
        return {}
    
    def document_delete_metadata(self, auth_context: Any, request: Any = None) -> Dict[str, Any]:
        """No-op metadata extraction."""
        return {}
    
    def document_update_text_metadata(self, auth_context: Any, request: Any = None) -> Dict[str, Any]:
        """No-op metadata extraction."""
        return {}
    
    def document_update_file_metadata(self, auth_context: Any, request: Any = None) -> Dict[str, Any]:
        """No-op metadata extraction."""
        return {}
    
    def document_update_metadata_resolver(self, auth_context: Any, request: Any = None) -> Dict[str, Any]:
        """No-op metadata extraction."""
        return {}
    
    def ingest_metadata(self, auth_context: Any, request: Any = None) -> Dict[str, Any]:
        """No-op metadata extraction."""
        return {}
    
    def ingest_text_metadata(self, auth_context: Any, request: Any = None) -> Dict[str, Any]:
        """No-op metadata extraction."""
        return {}
    
    def ingest_file_metadata(self, auth_context: Any, request: Any = None) -> Dict[str, Any]:
        """No-op metadata extraction."""
        return {}
    
    def batch_ingest_metadata(self, auth_context: Any, request: Any = None) -> Dict[str, Any]:
        """No-op metadata extraction."""
        return {}
    
    def retrieve_metadata(self, auth_context: Any, request: Any = None) -> Dict[str, Any]:
        """No-op metadata extraction."""
        return {}
    
    def retrieve_chunks_metadata(self, auth_context: Any, request: Any = None) -> Dict[str, Any]:
        """No-op metadata extraction."""
        return {}
    
    def retrieve_docs_metadata(self, auth_context: Any, request: Any = None) -> Dict[str, Any]:
        """No-op metadata extraction."""
        return {}
    
    def search_documents_metadata(self, auth_context: Any, request: Any = None) -> Dict[str, Any]:
        """No-op metadata extraction."""
        return {}
    
    def batch_documents_metadata(self, auth_context: Any, request: Any = None) -> Dict[str, Any]:
        """No-op metadata extraction."""
        return {}
    
    def batch_chunks_metadata(self, auth_context: Any, request: Any = None) -> Dict[str, Any]:
        """No-op metadata extraction."""
        return {}
    
    def create_folder_metadata(self, auth_context: Any, request: Any = None) -> Dict[str, Any]:
        """No-op metadata extraction."""
        return {}
    
    def list_folders_metadata(self, auth_context: Any, request: Any = None) -> Dict[str, Any]:
        """No-op metadata extraction."""
        return {}
    
    def add_document_to_folder_metadata(self, auth_context: Any, request: Any = None) -> Dict[str, Any]:
        """No-op metadata extraction."""
        return {}
    
    def remove_document_from_folder_metadata(self, auth_context: Any, request: Any = None) -> Dict[str, Any]:
        """No-op metadata extraction."""
        return {}
    
    def get_folder_metadata(self, auth_context: Any, request: Any = None) -> Dict[str, Any]:
        """No-op metadata extraction."""
        return {}
    
    def delete_folder_metadata(self, auth_context: Any, request: Any = None) -> Dict[str, Any]:
        """No-op metadata extraction."""
        return {}
    
    def create_graph_metadata(self, auth_context: Any, request: Any = None) -> Dict[str, Any]:
        """No-op metadata extraction."""
        return {}
    
    def get_graph_metadata(self, auth_context: Any, request: Any = None) -> Dict[str, Any]:
        """No-op metadata extraction."""
        return {}
    
    def list_graphs_metadata(self, auth_context: Any, request: Any = None) -> Dict[str, Any]:
        """No-op metadata extraction."""
        return {}
    
    def update_graph_metadata(self, auth_context: Any, request: Any = None) -> Dict[str, Any]:
        """No-op metadata extraction."""
        return {}
    
    def workflow_status_metadata(self, auth_context: Any, request: Any = None) -> Dict[str, Any]:
        """No-op metadata extraction."""
        return {}
