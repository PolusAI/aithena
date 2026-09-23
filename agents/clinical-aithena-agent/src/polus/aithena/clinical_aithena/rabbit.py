"""RabbitMQ publisher and subscriber for GARDIAN real-time status updates.

Publishes pipeline progress messages to a RabbitMQ topic exchange and
provides a subscriber that yields messages for a given session – used
by the FastAPI WebSocket endpoint to relay updates to the browser.
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import AsyncIterator, Optional

import aio_pika
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# Exchange / routing constants
EXCHANGE_NAME = "clinical-aithena-exchange"

# Status message constants for the GARDIAN pipeline
STATUS_GENERATING_KEYWORDS = "generating_keywords"
STATUS_GENERATING_EMBEDDING = "generating_embedding"
STATUS_RETRIEVING_TRIALS = "retrieving_trials"
STATUS_MATCHING_CRITERIA = "matching_criteria"
STATUS_MATCHING_TRIAL = "matching_trial"
STATUS_RANKING_TRIALS = "ranking_trials"
STATUS_RESPONDING = "responding"

# User-friendly message templates
STATUS_MESSAGES = {
    STATUS_GENERATING_KEYWORDS: "Analyzing patient information and extracting key medical terms...",
    STATUS_GENERATING_EMBEDDING: "Creating semantic representation of patient case...",
    STATUS_RETRIEVING_TRIALS: "Searching database for relevant clinical trials...",
    STATUS_MATCHING_CRITERIA: "Analyzing eligibility criteria for candidate trials...",
    STATUS_MATCHING_TRIAL: "Evaluating trial compatibility...",
    STATUS_RANKING_TRIALS: "Calculating relevance and eligibility scores...",
    STATUS_RESPONDING: "Processing complete, presenting results...",
}


class ProcessingStatus(BaseModel):
    """Status message for GARDIAN pipeline processing."""

    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="Timestamp of the status update",
    )
    status: str = Field(..., description="Current processing status")
    message: Optional[str] = Field(None, description="Human-readable message")


class RabbitMQPublisher:
    """Publishes JSON status messages to a RabbitMQ topic exchange.

    Usage::

        publisher = RabbitMQPublisher()
        await publisher.connect("amqp://guest:guest@localhost/")
        await publisher.publish_status(session_id, "generating_keywords")
        await publisher.disconnect()
    """

    def __init__(self) -> None:
        self._connection: Optional[aio_pika.abc.AbstractRobustConnection] = None
        self._channel: Optional[aio_pika.abc.AbstractChannel] = None
        self._exchange: Optional[aio_pika.abc.AbstractExchange] = None

    @property
    def is_connected(self) -> bool:
        return (
            self._connection is not None
            and not self._connection.is_closed
            and self._channel is not None
            and not self._channel.is_closed
        )

    async def connect(self, url: str) -> None:
        """Open a robust connection and declare the topic exchange."""
        try:
            self._connection = await aio_pika.connect_robust(url)
            self._channel = await self._connection.channel()
            self._exchange = await self._channel.declare_exchange(
                EXCHANGE_NAME,
                aio_pika.ExchangeType.TOPIC,
                durable=True,
            )
            logger.info("RabbitMQ publisher connected to %s", url)
        except Exception:
            logger.warning(
                "RabbitMQ publisher failed to connect to %s – "
                "status updates will be unavailable",
                url,
                exc_info=True,
            )
            # Reset state so is_connected returns False
            self._connection = None
            self._channel = None
            self._exchange = None

    async def disconnect(self) -> None:
        """Gracefully close the connection."""
        if self._connection and not self._connection.is_closed:
            await self._connection.close()
            logger.info("RabbitMQ publisher disconnected")
        self._connection = None
        self._channel = None
        self._exchange = None

    async def publish_status(
        self,
        session_id: str,
        status: str,
        message: Optional[str] = None,
    ) -> None:
        """Publish a status update for *session_id*.

        If the publisher is not connected the call is silently ignored so
        that the pipeline can function without RabbitMQ.
        """
        if not self.is_connected or self._exchange is None:
            logger.warning("RabbitMQ not connected – skipping status update: %s", status)
            return

        if message is None:
            message = STATUS_MESSAGES.get(status, status)

        payload = ProcessingStatus(
            status=status,
            message=message,
        )

        routing_key = f"session.{session_id}"

        try:
            await self._exchange.publish(
                aio_pika.Message(
                    body=payload.model_dump_json().encode(),
                    content_type="application/json",
                ),
                routing_key=routing_key,
            )
            logger.info("Published status [%s] to %s", status, routing_key)
        except Exception:
            logger.warning(
                "Failed to publish status %s to %s",
                status,
                routing_key,
                exc_info=True,
            )

    @asynccontextmanager
    async def subscribe(self, session_id: str) -> AsyncIterator[asyncio.Queue]:
        """Subscribe to status updates for *session_id*.

        Creates an exclusive, auto-delete queue bound to the exchange with
        routing key ``session.<session_id>`` and yields an :class:`asyncio.Queue`
        that receives :class:`ProcessingStatus` JSON strings.

        Usage::

            async with publisher.subscribe("abc-123") as queue:
                while True:
                    msg = await asyncio.wait_for(queue.get(), timeout=300)
                    ...  # forward to WebSocket
        """
        if not self.is_connected or self._channel is None or self._exchange is None:
            raise RuntimeError("RabbitMQ publisher is not connected")

        routing_key = f"session.{session_id}"
        out_queue: asyncio.Queue[str] = asyncio.Queue()

        # Declare an exclusive, auto-delete queue (cleaned up when we leave)
        queue = await self._channel.declare_queue(exclusive=True, auto_delete=True)
        await queue.bind(self._exchange, routing_key=routing_key)
        logger.info("Subscribed to %s via temp queue %s", routing_key, queue.name)

        async def _on_message(message: aio_pika.abc.AbstractIncomingMessage) -> None:
            async with message.process():
                await out_queue.put(message.body.decode())

        consumer_tag = await queue.consume(_on_message)

        try:
            yield out_queue
        finally:
            await queue.cancel(consumer_tag)
            try:
                await queue.delete()
            except Exception:
                pass  # auto-delete may have already removed it
            logger.info("Unsubscribed from %s", routing_key)
