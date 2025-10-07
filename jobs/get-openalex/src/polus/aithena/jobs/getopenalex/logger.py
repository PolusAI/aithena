"""Local logger module to replace polus.aithena.common.logger dependency."""

import logging
import sys
from pathlib import Path

# Color codes for terminal output
COLORS = {
    "DEBUG": "\033[36m",    # Cyan
    "INFO": "\033[32m",     # Green
    "WARNING": "\033[33m",  # Yellow
    "ERROR": "\033[31m",    # Red
    "CRITICAL": "\033[35m", # Magenta
    "RESET": "\033[0m",     # Reset
}


class ColoredFormatter(logging.Formatter):
    """Custom formatter that adds colors to log output."""

    def __init__(self, *args, use_colors: bool = True, **kwargs):
        super().__init__(*args, **kwargs)
        self.use_colors = use_colors and sys.stderr.isatty()

    def format(self, record: logging.LogRecord) -> str:
        """Format the log record with colors if enabled."""
        if self.use_colors:
            levelname = record.levelname
            if levelname in COLORS:
                record.levelname = f"{COLORS[levelname]}{levelname}{COLORS['RESET']}"
        return super().format(record)


def get_logger(
    name: str | None = None,
    level: str = "INFO",
    use_colors: bool = True,
) -> logging.Logger:
    """Get a configured logger instance.
    
    Args:
        name: Logger name. If None, uses the root logger.
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        use_colors: Whether to use colored output for terminal.
    
    Returns:
        Configured logger instance.
    """
    # Get or create logger
    if name:
        # Clean up the name if it's a file path
        if "/" in name or "\\" in name:
            name = Path(name).stem
        logger = logging.getLogger(name)
    else:
        logger = logging.getLogger()
    
    # Only configure if not already configured
    if not logger.handlers:
        # Set level
        log_level = getattr(logging, level.upper(), logging.INFO)
        logger.setLevel(log_level)
        
        # Create console handler
        console_handler = logging.StreamHandler(sys.stderr)
        console_handler.setLevel(log_level)
        
        # Create formatter
        format_string = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        formatter = ColoredFormatter(
            format_string,
            datefmt="%Y-%m-%d %H:%M:%S",
            use_colors=use_colors,
        )
        console_handler.setFormatter(formatter)
        
        # Add handler to logger
        logger.addHandler(console_handler)
    
    return logger


# Create a default logger instance
logger = get_logger(__name__)
