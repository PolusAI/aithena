"""Logger module for Aithena."""

from . import config
import logging

logging.basicConfig(
    format="%(asctime)s - %(name)-8s - %(levelname)-8s - %(message)s",
    datefmt="%d-%b-%y %H:%M:%S",
)

# Factory for aithena loggers
def get_logger(file = "", log_level = config.AITHENA_LOG_LEVEL):
    logger = logging.getLogger(file)
    logger.setLevel(log_level)
    return logger

# Create a logger that logs the execution time of decorated functions
exec_time_logger = logging.getLogger('execution_time_logger')
exec_time_logger.setLevel(logging.INFO)
# Create a file handler
file_handler = logging.FileHandler('execution_time.log')
file_handler.setLevel(logging.INFO)
# Create a logging format
formatter = logging.Formatter("%(asctime)s - %(name)-8s - %(levelname)-8s - %(message)s")
file_handler.setFormatter(formatter)
# Add the file handler to the logger
exec_time_logger.addHandler(file_handler)