"""Embedding service."""
# TODO currently only support NvEmbed.
# Should we mix solara concern here as a sort of adapter layer?
# TODO decide fail recovery:
# should we prevent the app from running or run in degraded mode (with query service disabled?)

import solara
from polus.ai.services.embed.embed_nvembed import EmbedderNvEmbed
from .common import get_logger

logger = get_logger(__file__)

embedding_service_available = solara.reactive(False)
try:
    embedding_service = EmbedderNvEmbed(1)
    embedding_service_available.value = True
except:
    embedding_service = None
    logger.error("Could not instantiate embedding service.")
