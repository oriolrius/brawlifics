from typing import Callable, Any
import logging

logger = logging.getLogger(__name__)

def step(description: str, func: Any):
    """
    Execute a test step with logging.
    Accepts either a function or the result of a function call.
    """
    logger.info(f"[step] {description}")
    if callable(func):
        return func()
    return func
