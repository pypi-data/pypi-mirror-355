import torch
import inspect
import torch.nn as nn
from typing import Optional, Dict, Any, List



class Predefined_LossFunctions:
    """
    A class to fetch and manage all available loss functions from PyTorch.
    Categorizes loss functions and provides comprehensive access to PyTorch's loss function library.
    """
    
    def __init__(self):
        """Initialize the loss function fetcher and categorize available loss functions."""
        self.all_loss_functions = self._discover_loss_functions()
        self.categorized_losses = self._categorize_loss_functions()
    
    def _discover_loss_functions(self) -> List[str]:
        """Discover all available loss functions in torch.nn"""
        loss_functions = []
        
        for name in dir(nn):
            if not name.startswith('_'):
                attr = getattr(nn, name)
                if (inspect.isclass(attr) and 
                    issubclass(attr, nn.Module) and 
                    'loss' in name.lower()):
                    loss_functions.append(name)
        
        # Add additional known loss functions that might not follow naming convention
        additional_losses = [
            'KLDivLoss', 'PoissonNLLLoss', 'GaussianNLLLoss', 
            'MultiLabelMarginLoss', 'MultiLabelSoftMarginLoss',
            'MultiMarginLoss', 'SoftMarginLoss', 'CosineEmbeddingLoss'
        ]
        
        for loss in additional_losses:
            if hasattr(nn, loss) and loss not in loss_functions:
                loss_functions.append(loss)
        
        return sorted(loss_functions)
    
    def _categorize_loss_functions(self) -> Dict[str, List[str]]:
        """Categorize loss functions into regression, classification, and ranking types"""
        categorized = {
            'regression': [],
            'classification': [],
            'ranking': [],
            'other': []
        }
        
        # Regression loss functions (continuous values)[1][2]
        regression_losses = [
            'MSELoss', 'L1Loss', 'SmoothL1Loss', 'HuberLoss', 
            'PoissonNLLLoss', 'GaussianNLLLoss'
        ]
        
        # Classification loss functions (discrete values)[1][2]
        classification_losses = [
            'CrossEntropyLoss', 'NLLLoss', 'BCELoss', 'BCEWithLogitsLoss',
            'MultiLabelMarginLoss', 'MultiLabelSoftMarginLoss', 'MultiMarginLoss',
            'SoftMarginLoss'
        ]
        
        # Ranking loss functions (relative distances)[1][2]
        ranking_losses = [
            'TripletMarginLoss', 'TripletMarginWithDistanceLoss', 'MarginRankingLoss',
            'HingeEmbeddingLoss', 'CosineEmbeddingLoss'
        ]
        
        for loss_name in self.all_loss_functions:
            if loss_name in regression_losses:
                categorized['regression'].append(loss_name)
            elif loss_name in classification_losses:
                categorized['classification'].append(loss_name)
            elif loss_name in ranking_losses:
                categorized['ranking'].append(loss_name)
            else:
                categorized['other'].append(loss_name)
        
        return categorized
    
    def fetch_loss_function(self, 
                           loss_name: str, 
                           **kwargs) -> nn.Module:
        """
        Fetch a loss function from torch.nn.
        
        Args:
            loss_name: Name of the loss function
            **kwargs: Additional arguments for loss function initialization
            
        Returns:
            Instantiated loss function
            
        Raises:
            ValueError: If loss function is not found
            RuntimeError: If loss function initialization fails
        """
        
        if loss_name not in self.all_loss_functions:
            available_count = len(self.all_loss_functions)
            raise ValueError(
                f"Loss function '{loss_name}' not found in torch.nn. "
                f"Available loss functions ({available_count} total):\n"
                f"- Regression: {len(self.categorized_losses['regression'])} functions\n"
                f"- Classification: {len(self.categorized_losses['classification'])} functions\n"
                f"- Ranking: {len(self.categorized_losses['ranking'])} functions\n"
                f"- Other: {len(self.categorized_losses['other'])} functions\n"
                f"Use list_available_losses() to see all available loss functions."
            )
        
        try:
            loss_class = getattr(nn, loss_name)
            return loss_class(**kwargs)
        except Exception as e:
            raise RuntimeError(
                f"Failed to instantiate loss function '{loss_name}' with kwargs {kwargs}. "
                f"Error: {e}"
            )
    
    def list_available_losses(self) -> Dict[str, List[str]]:
        """List all available loss functions categorized by type"""
        return self.categorized_losses.copy()
    
    def search_loss_function(self, query: str) -> Dict[str, List[str]]:
        """Search for loss functions containing the query string"""
        results = {
            'regression': [],
            'classification': [],
            'ranking': [],
            'other': []
        }
        
        query_lower = query.lower()
        
        for category, losses in self.categorized_losses.items():
            for loss in losses:
                if query_lower in loss.lower():
                    results[category].append(loss)
        
        return results
    
    def get_loss_info(self, loss_name: str) -> Dict[str, Any]:
        """Get detailed information about a specific loss function"""
        if loss_name not in self.all_loss_functions:
            return {'found': False, 'error': f"Loss function '{loss_name}' not found"}
        
        # Determine category
        category = 'other'
        for cat, losses in self.categorized_losses.items():
            if loss_name in losses:
                category = cat
                break
        
        # Get class and docstring
        loss_class = getattr(nn, loss_name)
        docstring = loss_class.__doc__ or "No documentation available"
        
        # Get constructor parameters
        try:
            sig = inspect.signature(loss_class.__init__)
            parameters = list(sig.parameters.keys())[1:]  # Exclude 'self'
        except:
            parameters = []
        
        return {
            'found': True,
            'name': loss_name,
            'category': category,
            'class': loss_class,
            'parameters': parameters,
            'docstring': docstring.split('\n')[0] if docstring else "No description",
            'module': 'torch.nn'
        }
    
    def get_losses_by_category(self, category: str) -> List[str]:
        """Get all loss functions in a specific category"""
        valid_categories = ['regression', 'classification', 'ranking', 'other']
        if category not in valid_categories:
            raise ValueError(f"Invalid category '{category}'. Valid categories: {valid_categories}")
        
        return self.categorized_losses[category].copy()
    
    def create_combined_loss(self, 
                           loss_configs: Dict[str, Dict[str, Any]], 
                           weights: Optional[Dict[str, float]] = None) -> 'CombinedLoss':
        """
        Create a combined loss function from multiple loss functions[5].
        
        Args:
            loss_configs: Dictionary mapping loss names to their configurations
            weights: Optional weights for each loss component
            
        Returns:
            Combined loss function instance
        """
        return CombinedLoss(self, loss_configs, weights)
    

class CombinedLoss(nn.Module):
    """A class for combining multiple loss functions with optional weights[5]"""
    
    def __init__(self, 
                 fetcher: Predefined_LossFunctions,
                 loss_configs: Dict[str, Dict[str, Any]], 
                 weights: Optional[Dict[str, float]] = None):
        super().__init__()
        self.fetcher = fetcher
        self.loss_functions = {}
        self.weights = weights or {}
        
        # Create loss function instances
        for name, config in loss_configs.items():
            self.loss_functions[name] = fetcher.fetch_loss_function(**config)
            if name not in self.weights:
                self.weights[name] = 1.0
    
    def forward(self, predictions, targets, **kwargs):
        """Compute combined loss"""
        total_loss = 0.0
        loss_details = {}
        
        for name, loss_fn in self.loss_functions.items():
            loss_value = loss_fn(predictions, targets)
            weighted_loss = self.weights[name] * loss_value
            total_loss += weighted_loss
            loss_details[name] = loss_value.item()
        
        return total_loss, loss_details