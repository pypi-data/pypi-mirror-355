"""Core functionality for the Puppet module."""

class PuppetModel:
    """Base class for all Puppet AI models.
    
    This class provides the foundation for creating, training, and using
    AI models with the Puppet framework.
    """
    
    def __init__(self, model_name: str = None):
        """Initialize a new PuppetModel instance.
        
        Args:
            model_name: Optional name for the model. If not provided,
                      a default name will be generated.
        """
        self.model_name = model_name or f"puppet_model_{id(self)}"
        self.is_trained = False
    
    def train(self, data, **kwargs):
        """Train the model on the provided data.
        
        Args:
            data: Training data. The exact format depends on the model type.
            **kwargs: Additional training parameters.
            
        Returns:
            dict: Training metrics and results.
        """
        raise NotImplementedError("Subclasses must implement train() method.")
    
    def predict(self, input_data):
        """Generate predictions for the input data.
        
        Args:
            input_data: Input data to generate predictions for.
            
        Returns:
            Model predictions.
        """
        if not self.is_trained:
            raise RuntimeError("Model must be trained before making predictions.")
        raise NotImplementedError("Subclasses must implement predict() method.")
    
    def save(self, path: str):
        """Save the model to disk.
        
        Args:
            path: Directory path where the model should be saved.
        """
        raise NotImplementedError("Subclasses must implement save() method.")
    
    @classmethod
    def load(cls, path: str):
        """Load a model from disk.
        
        Args:
            path: Path to the saved model directory.
            
        Returns:
            PuppetModel: Loaded model instance.
        """
        raise NotImplementedError("Subclasses must implement load() method.")
