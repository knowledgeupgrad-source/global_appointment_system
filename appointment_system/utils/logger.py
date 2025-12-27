import logging
import os
from ..utils.settings import SETTINGS

def setup_logging():
    """Set up application logging"""
    logging.basicConfig(
        level=getattr(logging, SETTINGS.logging_level, logging.DEBUG),
        format='%(asctime)s - %(levelname)s - %(name)s - %(funcName)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    return logging.getLogger("appointment-system")

logger = setup_logging()