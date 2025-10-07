"""Common RabbitMQ utilities."""

from pydantic import BaseModel, Field
import datetime
from faststream.rabbit import RabbitExchange, RabbitQueue, ExchangeType
from typing import Optional

ask_aithena_exchange = RabbitExchange(
    "ask-aithena-exchange",
    ExchangeType.TOPIC,
    durable=True,
)

ask_aithena_queue = RabbitQueue(
    "ask-aithena-queue",
    routing_key="session.{session_id}",
)


class ProcessingStatus(BaseModel):
    """Status message for query processing."""

    timestamp: str = Field(
        ...,
        description="Timestamp of the status update",
        default_factory=lambda: datetime.datetime.now().isoformat(),
    )
    status: str = Field(..., description="Current processing status")
    message: Optional[str] = Field(None, description="Current processing message")
