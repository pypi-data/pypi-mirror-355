import logging
import sys

import logfire
from loguru import logger

# Remove existing handlers
for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)


class InterceptHandler(logging.Handler):
    def emit(self, record):
        # Get corresponding Loguru level
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Find caller to get correct stack depth
        frame, depth = logging.currentframe(), 2
        while frame.f_back and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )


# Intercept standard logging
logging.basicConfig(handlers=[InterceptHandler()], level=logging.INFO)


def configure_logging(verbosity: int):
    """
    Configures the Loguru logger based on the specified verbosity level.

    Removes the default handler and adds a stderr handler with the appropriate
    log level (ERROR, WARNING, INFO, DEBUG, or TRACE).

    Args:
        verbosity: An integer representing the desired verbosity level (0-3+).
    """
    logger.remove()  # Remove default handler
    if verbosity == 0:
        log_level = "ERROR"
    elif verbosity == 1:
        log_level = "WARNING"
    elif verbosity == 2:
        log_level = "INFO"
    elif verbosity == 3:
        log_level = "DEBUG"
    elif verbosity >= 4:
        log_level = "TRACE"
    else:
        log_level = "ERROR"
    
    logger.add(sys.stderr, level=log_level)
    if verbosity > 0:  # Only log the debug message if verbosity > 0
        logger.debug(f"Log level set to {log_level}")

    # Clear specific loggers to prevent duplicate logs and ensure proper logging via loguru
    loggers = (
        "uvicorn",
        "uvicorn.access", 
        "uvicorn.error",
        "fastapi",
        "asyncio",
        "starlette",
        "httpx",
        "celery",
        "celery.worker",
        "celery.task",
        "kombu",
    )

    for logger_name in loggers:
        logging_logger = logging.getLogger(logger_name)
        logging_logger.handlers = []
        logging_logger.propagate = True
        if verbosity == 0:
            logging_logger.setLevel(logging.CRITICAL)
