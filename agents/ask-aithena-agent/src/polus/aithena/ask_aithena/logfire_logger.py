"""Logfire logger for Ask Aithena Agent."""

from polus.aithena.ask_aithena.config import USE_LOGFIRE
from typing import Optional
if USE_LOGFIRE:
    import logfire as original_logfire
    original_logfire.configure()
    logfire = original_logfire
else:
    class logfire:
        @staticmethod
        def info(*args, **kwargs) -> None:
            pass
        
        @staticmethod
        def error(*args, **kwargs) -> None:
            pass
        
        @staticmethod
        def instrument_httpx(*args, **kwargs) -> None:
            pass
        @staticmethod
        def configure(*args, **kwargs) -> None:
            pass

        @staticmethod
        def instrument_openai(*args, **kwargs) -> None:
            pass

        @staticmethod
        def instrument_fastapi(*args, **kwargs) -> None:
            pass
