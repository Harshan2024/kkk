"""
app/queue/task_queue.py — CarbonTracker Message Queue Abstraction
=================================================================
Phase 15: Message Queue Readiness

Provides a pluggable task queue interface that currently runs in-process.
Future integrations can swap to RabbitMQ or Kafka by implementing the
AbstractTaskQueue interface and setting QUEUE_BACKEND env var.

Architecture:
    AbstractTaskQueue (ABC)
    ├── InProcessTaskQueue   ← default (threading.Thread, zero dependencies)
    ├── RabbitMQTaskQueue    ← stub (activated by RABBITMQ_URL)
    └── KafkaTaskQueue       ← stub (activated by KAFKA_BOOTSTRAP_SERVERS)

Usage:
    from app.queue.task_queue import get_queue, TaskMessage, TaskPriority

    queue = get_queue()

    # Enqueue a background job
    queue.enqueue(TaskMessage(
        task_type="send_weekly_report",
        payload={"user_id": 123, "period": "2024-W27"},
        priority=TaskPriority.LOW,
    ))

    # Check queue health
    status = queue.status()
"""

import os
import logging
import threading
import time
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import IntEnum
from queue import PriorityQueue, Empty
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger("carbontracker.queue")


# ─── Task Priority ────────────────────────────────────────────────────────────
class TaskPriority(IntEnum):
    CRITICAL = 0   # Executed immediately
    HIGH     = 1   # Security/auth events
    NORMAL   = 2   # Standard background work
    LOW      = 3   # Analytics, reports, emails


# ─── Task Message ─────────────────────────────────────────────────────────────
@dataclass(order=True)
class TaskMessage:
    """
    Represents a single unit of work to be processed by the queue.
    Messages are ordered by (priority, enqueued_at) for fair scheduling.
    """
    priority:    TaskPriority = field(default=TaskPriority.NORMAL)
    enqueued_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat(), compare=True)
    task_id:     str = field(default_factory=lambda: str(uuid.uuid4()), compare=False)
    task_type:   str = field(default="generic", compare=False)
    payload:     Dict[str, Any] = field(default_factory=dict, compare=False)
    retries:     int = field(default=0, compare=False)
    max_retries: int = field(default=3, compare=False)

    def to_dict(self) -> dict:
        return {
            "task_id": self.task_id,
            "task_type": self.task_type,
            "priority": self.priority.name,
            "payload": self.payload,
            "enqueued_at": self.enqueued_at,
            "retries": self.retries,
            "max_retries": self.max_retries,
        }


# ─── Handler Registry ─────────────────────────────────────────────────────────
_handlers: Dict[str, Callable[[TaskMessage], None]] = {}


def register_handler(task_type: str):
    """Decorator to register a function as a task handler."""
    def decorator(fn: Callable):
        _handlers[task_type] = fn
        logger.info(f"[TaskQueue] Registered handler for task_type='{task_type}'")
        return fn
    return decorator


# ─── Abstract Queue Interface ─────────────────────────────────────────────────
class AbstractTaskQueue(ABC):

    @abstractmethod
    def enqueue(self, message: TaskMessage) -> str:
        """Add a task to the queue. Returns task_id."""
        ...

    @abstractmethod
    def status(self) -> dict:
        """Return queue health and statistics."""
        ...

    @abstractmethod
    def start(self):
        """Start the consumer worker(s)."""
        ...

    @abstractmethod
    def stop(self):
        """Gracefully stop worker(s)."""
        ...


# ─── In-Process Queue (default) ───────────────────────────────────────────────
class InProcessTaskQueue(AbstractTaskQueue):
    """
    Thread-based in-process task queue.
    Uses a PriorityQueue to respect TaskPriority ordering.
    This is the production default — zero external dependencies.
    """

    def __init__(self, worker_count: int = 2, max_queue_size: int = 500):
        self._queue: PriorityQueue = PriorityQueue(maxsize=max_queue_size)
        self._workers: List[threading.Thread] = []
        self._worker_count = worker_count
        self._running = False
        self._lock = threading.Lock()
        self._stats = {
            "enqueued": 0,
            "processed": 0,
            "failed": 0,
            "retried": 0,
        }

    def enqueue(self, message: TaskMessage) -> str:
        try:
            self._queue.put_nowait(message)
            with self._lock:
                self._stats["enqueued"] += 1
            logger.info(
                f"[TaskQueue] Enqueued task_id={message.task_id} "
                f"type={message.task_type} priority={message.priority.name}"
            )
            return message.task_id
        except Exception as e:
            logger.error(f"[TaskQueue] Failed to enqueue {message.task_id}: {e}")
            raise

    def _process_one(self, message: TaskMessage):
        handler = _handlers.get(message.task_type)
        if not handler:
            logger.warning(f"[TaskQueue] No handler for task_type='{message.task_type}'")
            return

        try:
            handler(message)
            with self._lock:
                self._stats["processed"] += 1
            logger.info(f"[TaskQueue] ✅ Completed task_id={message.task_id} type={message.task_type}")
        except Exception as e:
            with self._lock:
                self._stats["failed"] += 1
            logger.error(f"[TaskQueue] ❌ Task {message.task_id} failed: {e}")

            # Retry logic
            if message.retries < message.max_retries:
                message.retries += 1
                delay = 2 ** message.retries  # Exponential backoff: 2s, 4s, 8s
                logger.info(f"[TaskQueue] Retrying task {message.task_id} in {delay}s (attempt {message.retries})")
                time.sleep(delay)
                self._queue.put_nowait(message)
                with self._lock:
                    self._stats["retried"] += 1
            else:
                logger.error(f"[TaskQueue] Task {message.task_id} exhausted {message.max_retries} retries — dropping.")

    def _worker_loop(self):
        while self._running:
            try:
                message = self._queue.get(timeout=1.0)
                self._process_one(message)
                self._queue.task_done()
            except Empty:
                continue
            except Exception as e:
                logger.error(f"[TaskQueue] Worker error: {e}")

    def start(self):
        self._running = True
        for i in range(self._worker_count):
            t = threading.Thread(
                target=self._worker_loop,
                name=f"task-worker-{i}",
                daemon=True
            )
            t.start()
            self._workers.append(t)
        logger.info(f"[TaskQueue] Started {self._worker_count} in-process worker(s)")

    def stop(self):
        self._running = False
        for t in self._workers:
            t.join(timeout=5)
        self._workers.clear()
        logger.info("[TaskQueue] Stopped all workers")

    def status(self) -> dict:
        with self._lock:
            stats = dict(self._stats)
        return {
            "backend": "in-process",
            "status": "running" if self._running else "stopped",
            "queue_size": self._queue.qsize(),
            "worker_count": self._worker_count,
            "registered_handlers": list(_handlers.keys()),
            **stats,
        }


# ─── RabbitMQ Adapter (stub) ──────────────────────────────────────────────────
class RabbitMQTaskQueue(AbstractTaskQueue):
    """
    RabbitMQ adapter stub.

    To activate:
    1. Set RABBITMQ_URL=amqp://user:pass@localhost:5672/
    2. Install: pip install pika
    3. Uncomment the pika connection code below.
    """

    def __init__(self, url: str):
        self._url = url
        self._available = False
        try:
            import pika  # noqa
            # self._connection = pika.BlockingConnection(pika.URLParameters(url))
            # self._channel = self._connection.channel()
            # self._channel.queue_declare(queue="carbontracker_tasks", durable=True)
            logger.info(f"[RabbitMQ STUB] Would connect to {url}")
        except ImportError:
            logger.error("[RabbitMQ] pika not installed. Run: pip install pika")

    def enqueue(self, message: TaskMessage) -> str:
        logger.info(f"[RabbitMQ STUB] Would enqueue task_id={message.task_id}")
        return message.task_id

    def status(self) -> dict:
        return {"backend": "rabbitmq", "status": "stub", "url": self._url}

    def start(self):
        pass

    def stop(self):
        pass


# ─── Kafka Adapter (stub) ─────────────────────────────────────────────────────
class KafkaTaskQueue(AbstractTaskQueue):
    """
    Apache Kafka adapter stub.

    To activate:
    1. Set KAFKA_BOOTSTRAP_SERVERS=localhost:9092
    2. Set KAFKA_TOPIC=carbontracker-tasks
    3. Install: pip install kafka-python
    4. Uncomment producer/consumer code below.
    """

    def __init__(self, bootstrap_servers: str, topic: str = "carbontracker-tasks"):
        self._servers = bootstrap_servers
        self._topic = topic
        try:
            from kafka import KafkaProducer  # noqa
            logger.info(f"[Kafka STUB] Would connect to {bootstrap_servers}, topic={topic}")
        except ImportError:
            logger.error("[Kafka] kafka-python not installed. Run: pip install kafka-python")

    def enqueue(self, message: TaskMessage) -> str:
        logger.info(f"[Kafka STUB] Would produce to topic={self._topic} task_id={message.task_id}")
        return message.task_id

    def status(self) -> dict:
        return {"backend": "kafka", "status": "stub", "servers": self._servers, "topic": self._topic}

    def start(self):
        pass

    def stop(self):
        pass


# ─── Built-in Task Handlers ───────────────────────────────────────────────────

@register_handler("send_welcome_email")
def handle_welcome_email(msg: TaskMessage):
    """Placeholder: Send welcome email after registration."""
    logger.info(f"[TASK] send_welcome_email for user_id={msg.payload.get('user_id')}")


@register_handler("generate_weekly_report")
def handle_weekly_report(msg: TaskMessage):
    """Placeholder: Generate and email weekly carbon footprint report."""
    logger.info(f"[TASK] generate_weekly_report for user_id={msg.payload.get('user_id')}")


@register_handler("recalculate_analytics")
def handle_recalculate_analytics(msg: TaskMessage):
    """Placeholder: Recalculate analytics after bulk activity import."""
    logger.info(f"[TASK] recalculate_analytics for user_id={msg.payload.get('user_id')}")


@register_handler("send_alert")
def handle_send_alert(msg: TaskMessage):
    """Route an alert through the notification system."""
    from app.utils.notifier import send_notification, NotificationEvent, NotificationLevel
    level_str = msg.payload.get("level", "info")
    try:
        level = NotificationLevel(level_str)
    except ValueError:
        level = NotificationLevel.INFO
    event = NotificationEvent(
        level=level,
        title=msg.payload.get("title", "CarbonTracker Alert"),
        message=msg.payload.get("message", ""),
        context=msg.payload.get("context", {}),
    )
    send_notification(event)


# ─── Factory ──────────────────────────────────────────────────────────────────
_queue_instance: Optional[AbstractTaskQueue] = None
_queue_lock = threading.Lock()


def get_queue() -> AbstractTaskQueue:
    """
    Returns the active task queue singleton.
    Auto-selects backend based on environment variables:
    - RABBITMQ_URL → RabbitMQTaskQueue
    - KAFKA_BOOTSTRAP_SERVERS → KafkaTaskQueue
    - (default) → InProcessTaskQueue
    """
    global _queue_instance
    if _queue_instance is not None:
        return _queue_instance

    with _queue_lock:
        if _queue_instance is not None:
            return _queue_instance

        rabbitmq_url = os.getenv("RABBITMQ_URL", "")
        kafka_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "")

        if rabbitmq_url:
            q = RabbitMQTaskQueue(rabbitmq_url)
        elif kafka_servers:
            q = KafkaTaskQueue(kafka_servers, os.getenv("KAFKA_TOPIC", "carbontracker-tasks"))
        else:
            q = InProcessTaskQueue(
                worker_count=int(os.getenv("TASK_WORKER_COUNT", "2")),
                max_queue_size=int(os.getenv("TASK_QUEUE_MAX_SIZE", "500")),
            )
            q.start()

        _queue_instance = q
        return _queue_instance
