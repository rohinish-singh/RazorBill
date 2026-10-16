"""Bounded asynchronous candidate classification worker."""

from __future__ import annotations

from concurrent.futures import Future, ThreadPoolExecutor
from threading import BoundedSemaphore, Lock
from typing import Any

from .classifier import CandidateClassifier


class BoundedClassifierWorker:
    def __init__(self, classifier: CandidateClassifier, *, max_workers: int = 1, max_pending: int = 4):
        if max_workers < 1 or max_pending < 0:
            raise ValueError("max_workers must be positive and max_pending non-negative")
        self.classifier = classifier
        self._executor = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="vlm-classifier")
        self._slots = BoundedSemaphore(max_workers + max_pending)
        self._rejected_count = 0
        self._counter_lock = Lock()

    @property
    def rejected_count(self) -> int:
        with self._counter_lock:
            return self._rejected_count

    def submit(self, candidate: dict[str, Any]) -> Future | None:
        """Submit without waiting; return None and count the drop when capacity is full."""
        if not self._slots.acquire(blocking=False):
            with self._counter_lock:
                self._rejected_count += 1
            return None
        try:
            future = self._executor.submit(self.classifier.classify_candidate, candidate)
        except BaseException:
            self._slots.release()
            raise
        future.add_done_callback(lambda _: self._slots.release())
        return future

    def try_submit(self, candidate: dict[str, Any]) -> Future | None:
        """Explicit capture-loop alias for the non-raising bounded submit operation."""
        return self.submit(candidate)

    def shutdown(self, *, wait: bool = True, cancel_futures: bool = False) -> None:
        self._executor.shutdown(wait=wait, cancel_futures=cancel_futures)
