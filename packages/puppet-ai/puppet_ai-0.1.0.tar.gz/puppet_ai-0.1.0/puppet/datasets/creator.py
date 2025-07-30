"""
Dataset creator module for Puppet AI.

Provides functionality to create datasets programmatically.
"""

import os
import json
import random
from datetime import datetime
from typing import List, Dict, Any, Optional

class DatasetCreator:
    """Handles the creation of datasets for machine learning tasks."""
    
    _instance = None
    _base_dir = "datasets"
    
    def __new__(cls, base_dir: str = None):
        if cls._instance is None:
            cls._instance = super(DatasetCreator, cls).__new__(cls)
            if base_dir:
                cls._base_dir = base_dir
            os.makedirs(cls._base_dir, exist_ok=True)
        return cls._instance
    
    def __init__(self, base_dir: str = None):
        """Initialize the DatasetCreator.
        
        Args:
            base_dir: Base directory to save datasets. Uses last set directory.
        """
        if base_dir and base_dir != self._base_dir:
            self._base_dir = base_dir
            os.makedirs(self._base_dir, exist_ok=True)
    
    @classmethod
    def set_base_dir(cls, base_dir: str):
        """Set the base directory for saving datasets.
        
        Args:
            base_dir: Directory path where datasets will be saved.
        """
        cls._base_dir = base_dir
        os.makedirs(base_dir, exist_ok=True)
        return cls._instance or cls()
    
    @property
    def base_dir(self):
        """Get the current base directory for datasets."""
        return self._base_dir
    
    def create_dataset(self, topic: str, num_samples: int = 1) -> List[Dict[str, Any]]:
        """Create a dataset about the given topic.
        
        Args:
            topic: The topic to create the dataset about.
            num_samples: Number of samples to generate.
            
        Returns:
            List of generated data samples.
        """
        samples = []
        for _ in range(num_samples):
            sample = {
                "id": len(os.listdir(self.base_dir)) + 1,
                "topic": topic,
                "content": f"This is a sample data about {topic}.",
                "created_at": datetime.now().isoformat(),
                "metadata": {
                    "source": "puppet-ai",
                    "version": "0.1.0"
                }
            }
            samples.append(sample)
        return samples
    
    def save_dataset(self, samples: List[Dict[str, Any]], filename: Optional[str] = None) -> str:
        """Save the dataset to a file.
        
        Args:
            samples: List of data samples to save.
            filename: Optional custom filename. If not provided, generates one.
            
        Returns:
            Path to the saved dataset file.
        """
        if not samples:
            raise ValueError("No samples provided to save.")
            
        if not filename:
            topic = samples[0]["topic"].replace(" ", "_").lower()
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"dataset_{topic}_{timestamp}.json"
        
        filepath = os.path.join(self.base_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump({"samples": samples}, f, indent=2)
            
        return filepath

def data(about: str) -> str:
    """Create a dataset about the specified topic.
    
    Args:
        about: The topic to create the dataset about.
        
    Returns:
        Path to the created dataset file.
    """
    creator = DatasetCreator()
    samples = creator.create_dataset(about)
    return creator.save_dataset(samples)

def timeIn_dataset(count: int) -> List[str]:
    """Create multiple datasets.
    
    Args:
        count: Number of datasets to create.
        
    Returns:
        List of paths to the created dataset files.
    """
    creator = DatasetCreator()
    result = []
    
    for i in range(count):
        topic = f"sample_topic_{i+1}"
        samples = creator.create_dataset(topic)
        filepath = creator.save_dataset(samples, f"dataset_batch_{i+1}.json")
        result.append(filepath)
    
    return result


def dataset_cometo(folder_name: str) -> None:
    """Set the directory where datasets will be saved.
    
    Args:
        folder_name: Directory path where datasets should be saved.
    """
    DatasetCreator.set_base_dir(folder_name)
