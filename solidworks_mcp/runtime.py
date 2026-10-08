"""Process-wide singleton for the COM worker and SolidWorks session.

The MCP server is a long-lived process that talks to exactly one SolidWorks
instance, so a single lazily-created session is shared by all tools.
"""

from __future__ import annotations

import threading
from typing import Optional

from .com.session import SolidWorksSession
from .com.worker import ComWorker
from .assembly import Assembly
from .batch import Batch
from .drawing import Drawing
from .modeling import Modeling

_lock = threading.Lock()
_worker: Optional[ComWorker] = None
_session: Optional[SolidWorksSession] = None
_modeling: Optional[Modeling] = None
_drawing: Optional[Drawing] = None
_assembly: Optional[Assembly] = None
_batch: Optional[Batch] = None


def get_session(visible: bool = True) -> SolidWorksSession:
    """Return the shared session, creating the worker on first use."""
    global _worker, _session
    with _lock:
        if _session is None:
            _worker = ComWorker()
            _session = SolidWorksSession(_worker, visible=visible)
        return _session


def get_modeling() -> Modeling:
    """Return the shared modeling helper bound to the shared session."""
    global _modeling
    session = get_session()
    with _lock:
        if _modeling is None:
            _modeling = Modeling(session)
        return _modeling


def get_drawing() -> Drawing:
    """Return the shared drawing helper bound to the shared session."""
    global _drawing
    session = get_session()
    with _lock:
        if _drawing is None:
            _drawing = Drawing(session)
        return _drawing


def get_assembly() -> Assembly:
    """Return the shared assembly helper bound to the shared session."""
    global _assembly
    session = get_session()
    with _lock:
        if _assembly is None:
            _assembly = Assembly(session)
        return _assembly


def get_batch() -> Batch:
    """Return the shared batch helper bound to the shared session."""
    global _batch
    session = get_session()
    with _lock:
        if _batch is None:
            _batch = Batch(session)
        return _batch


def shutdown() -> None:
    """Stop the worker thread and drop the session (used by tests)."""
    global _worker, _session, _modeling, _drawing, _assembly, _batch
    with _lock:
        if _worker is not None:
            _worker.stop()
        _worker = None
        _session = None
        _modeling = None
        _drawing = None
        _assembly = None
        _batch = None
