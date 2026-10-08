"""A single-threaded apartment (STA) worker for SolidWorks COM calls.

SolidWorks COM objects are created in an STA and are not free-threaded. Calling
them from arbitrary threads (e.g. directly inside an asyncio event loop, whose
threads are MTA) leads to marshalling errors or hard crashes. This worker owns
one dedicated STA thread and funnels *every* COM call through it, one at a
time, so the whole server can present a simple synchronous ``call`` API while
keeping all COM interaction on a single, stable apartment.
"""

from __future__ import annotations

import queue
import threading
import traceback
from typing import Any, Callable, Optional, TypeVar

import pythoncom

T = TypeVar("T")

# Sentinel placed on the queue to ask the worker to stop.
_STOP = object()


class ComError(RuntimeError):
    """Raised in the caller's thread when a COM call fails on the worker thread."""

    def __init__(self, message: str, original: BaseException, remote_traceback: str):
        super().__init__(message)
        self.original = original
        self.remote_traceback = remote_traceback


class ComWorker:
    """Serialize all COM work onto one apartment-threaded thread."""

    def __init__(self, name: str = "solidworks-com-sta") -> None:
        self._name = name
        self._queue: "queue.Queue[Any]" = queue.Queue()
        self._thread = threading.Thread(target=self._run, name=name, daemon=True)
        self._started = threading.Event()
        self._init_error: Optional[BaseException] = None
        self._thread.start()
        # Block until CoInitialize has run so the first call() is safe.
        self._started.wait()
        if self._init_error is not None:
            raise ComError(
                "COM apartment failed to initialize",
                self._init_error,
                traceback.format_exc(),
            )

    def _run(self) -> None:
        try:
            # A fresh thread with no prior COM init becomes an STA here.
            pythoncom.CoInitializeEx(pythoncom.COINIT_APARTMENTTHREADED)
        except BaseException as exc:  # pragma: no cover - startup failure path
            self._init_error = exc
            self._started.set()
            return
        self._started.set()
        try:
            while True:
                item = self._queue.get()
                if item is _STOP:
                    break
                fn, args, kwargs, result, done = item
                try:
                    result.append(("ok", fn(*args, **kwargs)))
                except BaseException as exc:  # noqa: BLE001 - relayed to caller
                    result.append(("err", exc, traceback.format_exc()))
                finally:
                    done.set()
        finally:
            pythoncom.CoUninitialize()

    def call(self, fn: Callable[..., T], *args: Any, **kwargs: Any) -> T:
        """Run ``fn(*args, **kwargs)`` on the STA thread and return its result.

        Exceptions raised on the worker thread are re-raised here, wrapped in
        :class:`ComError` with the remote traceback attached.
        """
        result: list = []
        done = threading.Event()
        self._queue.put((fn, args, kwargs, result, done))
        done.wait()
        outcome = result[0]
        if outcome[0] == "ok":
            return outcome[1]
        _, exc, remote_tb = outcome
        raise ComError(str(exc), exc, remote_tb) from exc

    def stop(self) -> None:
        """Ask the worker thread to exit (used on shutdown and in tests)."""
        if self._thread.is_alive():
            self._queue.put(_STOP)
            self._thread.join(timeout=5)
