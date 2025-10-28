import sys
import logging
from typing import Optional

from .data_structure import TreeNode, DAGNode, DAGEdge, DAGGraph


def get_logger(name: str, level: str = "INFO") -> logging.Logger:
    """Get a configured logger."""
    logger = logging.getLogger(name)

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    logger.setLevel(getattr(logging, level.upper()))
    return logger


__all__ = ["TreeNode", "DAGNode", "DAGEdge", "DAGGraph", "get_logger"]
