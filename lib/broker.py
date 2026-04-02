"""
In-memory publish-subscribe message broker.

Topics used in EU Custom Data Hub
──────────────────────────────────
"incoming"      raw transaction dict — published by the simulation loop
"stored"        same dict — published by the DB-store worker after INSERT
"alarm_fired"   {"tx": dict, "alarm_id": int, "alarm": dict | None}
                published by the alarm worker when a transaction is flagged
"""
from __future__ import annotations

import asyncio
from collections import defaultdict


class MessageBroker:
    """
    Simple fan-out broker.  Each call to subscribe() returns an independent
    asyncio.Queue so every subscriber receives every message on the topic.
    """

    def __init__(self) -> None:
        self._queues: dict[str, list[asyncio.Queue]] = defaultdict(list)

    # ── Subscription management ───────────────────────────────────────────────

    def subscribe(self, topic: str, maxsize: int = 500) -> asyncio.Queue:
        """Register as a subscriber for *topic*; returns a dedicated queue."""
        q: asyncio.Queue = asyncio.Queue(maxsize=maxsize)
        self._queues[topic].append(q)
        return q

    def unsubscribe(self, topic: str, q: asyncio.Queue) -> None:
        try:
            self._queues[topic].remove(q)
        except ValueError:
            pass

    # ── Publishing ────────────────────────────────────────────────────────────

    async def publish(self, topic: str, message) -> None:
        """Deliver *message* to every subscriber of *topic* (back-pressured)."""
        for q in self._queues[topic]:
            await q.put(message)

    def publish_nowait(self, topic: str, message) -> None:
        """Non-blocking publish; silently drops for any full subscriber queue."""
        for q in self._queues[topic]:
            try:
                q.put_nowait(message)
            except asyncio.QueueFull:
                pass

    # ── Introspection ─────────────────────────────────────────────────────────

    def subscriber_count(self, topic: str) -> int:
        return len(self._queues[topic])

    def qsize(self, topic: str) -> int:
        """Total pending messages across all subscriber queues for *topic*."""
        return sum(q.qsize() for q in self._queues[topic])


# Singleton used by api.py and workers
broker = MessageBroker()
