"""
Puppet - A Python module for creating and managing AI models.

This module provides tools for training, fine-tuning, and deploying AI models
with an easy-to-use interface.
"""

__version__ = "0.1.0"

# Import core functionality
from .core import PuppetModel
from .datasets import data, timeIn_dataset, dataset_cometo

__all__ = [
    'PuppetModel',
    'data',
    'timeIn_dataset',
    'dataset_cometo'
]
