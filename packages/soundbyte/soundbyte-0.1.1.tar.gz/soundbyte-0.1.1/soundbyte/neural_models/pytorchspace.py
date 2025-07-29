import torch
import inspect
import torchvision.models
import torchaudio.models
import torchaudio.pipelines
from typing import Dict, Any, Union


class Predefined_NeuralModels:
    """
    A class to fetch models from torchvision.models, torchaudio.models, and torchaudio.pipelines.
    Raises errors if models are not found and handles pretrained weight loading.
    """
    
    def __init__(self):
        """Initialize the model fetcher and discover available models."""
        self.torchvision_models = self._get_torchvision_models()
        self.torchaudio_models = self._get_torchaudio_models()
        self.torchaudio_pipelines = self._get_torchaudio_pipelines()
    
    def _get_torchvision_models(self):
        """Get available models from torchvision.models"""
        try:
            # Use the official list_models function if available
            return torchvision.models.list_models()
        except AttributeError:
            # Fallback method - filter lowercase function names
            models = []
            for name in dir(torchvision.models):
                if (not name.startswith('_') and 
                    name.islower() and 
                    callable(getattr(torchvision.models, name))):
                    models.append(name)
            return models
    
    def _get_torchaudio_models(self):
        """Get available model classes from torchaudio.models"""
        models = []
        for name in dir(torchaudio.models):
            if not name.startswith('_'):
                attr = getattr(torchaudio.models, name)
                if inspect.isclass(attr):
                    models.append(name)
        return models
    
    def _get_torchaudio_pipelines(self):
        """Get available pipelines from torchaudio.pipelines"""
        pipelines = []
        for name in dir(torchaudio.pipelines):
            if (not name.startswith('_') and 
                name.isupper() and 
                hasattr(getattr(torchaudio.pipelines, name), 'get_model')):
                pipelines.append(name)
        return pipelines
    
    def fetch_model(self, 
                   model_name: str, 
                   pretrained: bool, 
                   **kwargs) -> Union[torch.nn.Module, Any]:
        """
        Fetch a model from torchvision, torchaudio.models, or torchaudio.pipelines.
        
        Args:
            model_name: Name of the model to fetch
            pretrained: Whether to load pretrained weights
            **kwargs: Additional arguments for model initialization
            
        Returns:
            Instantiated model
            
        Raises:
            ValueError: If model is not found in any of the libraries
            RuntimeError: If model loading fails
        """
        
        # Search in torchvision models first
        if model_name in self.torchvision_models:
            return self._load_torchvision_model(model_name, pretrained, **kwargs)
        
        # Search in torchaudio models
        elif model_name in self.torchaudio_models:
            return self._load_torchaudio_model(model_name, pretrained, **kwargs)
        
        # Search in torchaudio pipelines
        elif model_name in self.torchaudio_pipelines:
            if not pretrained:
                print(f"Warning: {model_name} is a pipeline with pretrained weights. Loading with pretrained=True.")
            return self._load_torchaudio_pipeline(model_name, **kwargs)
        
        else:
            available_models = self.list_available_models()
            total_models = (len(available_models['torchvision']) + 
                          len(available_models['torchaudio_models']) + 
                          len(available_models['torchaudio_pipelines']))
            
            raise ValueError(
                f"Model '{model_name}' not found in any of the libraries. "
                f"Available models ({total_models} total):\n"
                f"- Torchvision: {len(available_models['torchvision'])} models\n"
                f"- Torchaudio models: {len(available_models['torchaudio_models'])} models\n"
                f"- Torchaudio pipelines: {len(available_models['torchaudio_pipelines'])} models\n"
                f"Use list_available_models() to see all available models."
            )
    
    def _load_torchvision_model(self, model_name: str, pretrained: bool, **kwargs):
        """Load a model from torchvision.models"""
        try:
            if pretrained:
                kwargs['weights'] = kwargs.get('weights', 'DEFAULT')
            else:
                kwargs['weights'] = None
            
            # Use get_model if available, otherwise use direct function call
            try:
                return torchvision.models.get_model(model_name, **kwargs)
            except AttributeError:
                model_fn = getattr(torchvision.models, model_name)
                return model_fn(**kwargs)
                
        except Exception as e:
            raise RuntimeError(
                f"Failed to load torchvision model '{model_name}' with pretrained={pretrained}. "
                f"Error: {e}"
            )
    
    def _load_torchaudio_model(self, model_name: str, pretrained: bool, **kwargs):
        """Load a model from torchaudio.models"""
        if pretrained:
            raise ValueError(
                f"Pretrained weights are not directly available for torchaudio.models.{model_name}. "
                f"Models in torchaudio.models are architecture definitions without pretrained weights. "
                f"Consider using torchaudio.pipelines for pretrained models, or set pretrained=False."
            )
        
        try:
            model_class = getattr(torchaudio.models, model_name)
            return model_class(**kwargs)
        except Exception as e:
            raise RuntimeError(
                f"Failed to instantiate torchaudio model '{model_name}'. "
                f"Error: {e}"
            )
    
    def _load_torchaudio_pipeline(self, pipeline_name: str, **kwargs):
        """Load a model from torchaudio.pipelines"""
        try:
            pipeline_bundle = getattr(torchaudio.pipelines, pipeline_name)
            return pipeline_bundle.get_model(**kwargs)
        except Exception as e:
            raise RuntimeError(
                f"Failed to load torchaudio pipeline '{pipeline_name}'. "
                f"Error: {e}"
            )
    
    def list_available_models(self) -> Dict[str, list]:
        """List all available models from all sources"""
        return {
            'torchvision': sorted(self.torchvision_models),
            'torchaudio_models': sorted(self.torchaudio_models),
            'torchaudio_pipelines': sorted(self.torchaudio_pipelines)
        }
    
    def search_model(self, query: str) -> Dict[str, list]:
        """Search for models containing the query string"""
        results = {
            'torchvision': [],
            'torchaudio_models': [],
            'torchaudio_pipelines': []
        }
        
        query_lower = query.lower()
        
        for model in self.torchvision_models:
            if query_lower in model.lower():
                results['torchvision'].append(model)
        
        for model in self.torchaudio_models:
            if query_lower in model.lower():
                results['torchaudio_models'].append(model)
        
        for model in self.torchaudio_pipelines:
            if query_lower in model.lower():
                results['torchaudio_pipelines'].append(model)
        
        return results
    
    def get_model_info(self, model_name: str) -> Dict[str, Any]:
        """Get information about where a model is located and its requirements"""
        info = {
            'found': False,
            'library': None,
            'supports_pretrained': False,
            'description': None
        }
        
        if model_name in self.torchvision_models:
            info.update({
                'found': True,
                'library': 'torchvision.models',
                'supports_pretrained': True,
                'description': 'Computer vision model with pretrained weights available'
            })
        elif model_name in self.torchaudio_models:
            info.update({
                'found': True,
                'library': 'torchaudio.models',
                'supports_pretrained': False,
                'description': 'Audio model architecture (no pretrained weights)'
            })
        elif model_name in self.torchaudio_pipelines:
            info.update({
                'found': True,
                'library': 'torchaudio.pipelines',
                'supports_pretrained': True,
                'description': 'Audio pipeline with pretrained weights and preprocessing'
            })
        
        return info