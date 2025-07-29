import torch
import torch.optim as optim
from typing import Optional, Dict, Any, Tuple



class Predefined_Optimizers_Schedulers:
    """
    A class to fetch and create optimizer-scheduler combinations from PyTorch.
    Falls back to Adam optimizer and StepLR scheduler if requested components are not found.
    """
    
    def __init__(self, 
                 model_parameters,
                 optimizer_name: str = "Adam",
                 scheduler_name: str = "StepLR",
                 optimizer_kwargs: Optional[Dict[str, Any]] = None,
                 scheduler_kwargs: Optional[Dict[str, Any]] = None):
        """
        Initialize the optimizer-scheduler combination.
        
        Args:
            model_parameters: Model parameters to optimize
            optimizer_name: Name of the optimizer (e.g., "Adam", "SGD")
            scheduler_name: Name of the scheduler (e.g., "StepLR", "LinearLR")
            optimizer_kwargs: Additional arguments for the optimizer
            scheduler_kwargs: Additional arguments for the scheduler
        """
        self.model_parameters = model_parameters
        self.optimizer_name = optimizer_name
        self.scheduler_name = scheduler_name
        self.optimizer_kwargs = optimizer_kwargs or {}
        self.scheduler_kwargs = scheduler_kwargs or {}
        
        # Default configurations
        self.default_optimizer = "Adam"
        self.default_scheduler = "ReduceLROnPlateau"
        self.default_optimizer_kwargs = {"lr": 0.001}
        self.default_scheduler_kwargs = {"mode": "min", "patience": 4}
        
        self.optimizer, self.scheduler = self._create_combo()
    
    def _get_optimizer_class(self, name: str):
        """Fetch optimizer class from torch.optim"""
        try:
            optimizer_class = getattr(optim, name)
            return optimizer_class
        except AttributeError:
            print(f"Optimizer '{name}' not found in torch.optim. Using default: {self.default_optimizer}")
            return getattr(optim, self.default_optimizer)
    
    def _get_scheduler_class(self, name: str):
        """Fetch scheduler class from torch.optim.lr_scheduler"""
        try:
            scheduler_class = getattr(optim.lr_scheduler, name)
            return scheduler_class
        except AttributeError:
            print(f"Scheduler '{name}' not found in torch.optim.lr_scheduler. Using default: {self.default_scheduler}")
            return getattr(optim.lr_scheduler, self.default_scheduler)
    
    def _create_combo(self) -> Tuple[torch.optim.Optimizer, torch.optim.lr_scheduler.LRScheduler]:
        """Create the optimizer-scheduler combination"""
        
        # Get optimizer class and create optimizer
        optimizer_class = self._get_optimizer_class(self.optimizer_name)
        
        # Use provided kwargs or defaults
        opt_kwargs = self.optimizer_kwargs if self.optimizer_kwargs else self.default_optimizer_kwargs
        
        try:
            optimizer = optimizer_class(self.model_parameters, **opt_kwargs)
        except Exception as e:
            print(f"Error creating optimizer with provided kwargs: {e}")
            print(f"Using default optimizer configuration")
            optimizer = getattr(optim, self.default_optimizer)(
                self.model_parameters, **self.default_optimizer_kwargs
            )
        
        # Get scheduler class and create scheduler
        scheduler_class = self._get_scheduler_class(self.scheduler_name)
        
        # Use provided kwargs or defaults
        sched_kwargs = self.scheduler_kwargs if self.scheduler_kwargs else self.default_scheduler_kwargs
        
        try:
            scheduler = scheduler_class(optimizer, **sched_kwargs)
        except Exception as e:
            print(f"Error creating scheduler with provided kwargs: {e}")
            print(f"Using default scheduler configuration")
            scheduler = getattr(optim.lr_scheduler, self.default_scheduler)(
                optimizer, **self.default_scheduler_kwargs
            )
        
        return optimizer, scheduler
    
    def step(self):
        self.optimizer.step()
    
    def scheduler_step(self):
        self.scheduler.step()
    
    def zero_grad(self):
        self.optimizer.zero_grad()
    
    def get_lr(self):
        return self.scheduler.get_last_lr()
    
    @classmethod
    def get_available_optimizers(cls):
        optimizer_names = []
        for name in dir(optim):
            attr = getattr(optim, name)
            if isinstance(attr, type) and issubclass(attr, torch.optim.Optimizer):
                optimizer_names.append(name)
        return optimizer_names
    
    @classmethod
    def get_available_schedulers(cls):
        scheduler_names = []
        for name in dir(optim.lr_scheduler):
            attr = getattr(optim.lr_scheduler, name)
            if isinstance(attr, type) and hasattr(attr, 'step'):
                scheduler_names.append(name)
        return scheduler_names