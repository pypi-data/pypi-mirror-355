"""
File:        desim/desim.py
Author:      Luis Enrique Arias Curbelo <lariasec@gmail.com> <github.com/larias95>
Created:     2025-06-14
Updated:     2025-06-14
Description: This module implements a Discrete Event Simulation (DES) framework
             for modeling systems where state changes occur at discrete points in time.
License:     MIT License (see LICENSE file)
"""

from abc import ABC, abstractmethod
from heapq import heappop, heappush
from typing import Any, Callable


class DiscreteEvent(ABC):
    def __init__(self, t: float):
        self.t = t
        self.cancelled = False

    def __lt__(self, other: "DiscreteEvent"):
        return self.t < other.t

    @abstractmethod
    def _run(self, env) -> list["DiscreteEvent"]: ...

    def _after(self, dt: float):
        return self.t + dt

    def cancel(self):
        self.cancelled = True


class DiscreteEventQueue:
    def __init__(self, t0: float = 0):
        self._events: list[DiscreteEvent] = []
        self.t = t0

    def empty(self):
        return len(self._events) == 0

    def step(self, env):
        self._skip_cancelled()

        if self.empty():
            return False

        e = heappop(self._events)
        self._check_no_time_travel(e)
        self.t = e.t
        self.add_events(e._run(env))

        return True

    def add_events(self, events: list[DiscreteEvent]):
        for e in events:
            heappush(self._events, e)

    def _skip_cancelled(self):
        while not self.empty() and self._events[0].cancelled:
            heappop(self._events)

    def _check_no_time_travel(self, e: DiscreteEvent):
        if e.t < self.t:
            raise ValueError("Time travel not allowed.")


def run_to(
    t: float,
    queue: DiscreteEventQueue,
    env,
    callback: Callable[[DiscreteEventQueue, Any], None] = None,
):
    while not queue.empty() and queue.t < t:
        if queue.step(env) and (callback is not None):
            callback(queue, env)


def run_to_end(
    queue: DiscreteEventQueue,
    env,
    callback: Callable[[DiscreteEventQueue, Any], None] = None,
):
    while not queue.empty():
        if queue.step(env) and (callback is not None):
            callback(queue, env)
