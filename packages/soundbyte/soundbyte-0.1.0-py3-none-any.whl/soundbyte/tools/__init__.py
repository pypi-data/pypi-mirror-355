import sys
import torch
import inspect
import importlib.util
from pathlib import Path



class FileComponentLoader:    
    def _load_module(self, file_path, module_suffix=""):
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"File {file_path} does not exist")

        if file_path.suffix != '.py':
            raise ValueError(f"File {file_path} is not a Python file")
        
        module_name = f"{file_path.stem}{module_suffix}"
        
        spec = importlib.util.spec_from_file_location(
            name=module_name,
            location=str(file_path)
        )
        
        if spec is None:
            raise ImportError(f"Could not load spec from {file_path}")

        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        return module
    
    def _get_available_items(self, module, item_type="class"):
        if item_type == "class":
            return [name for name in dir(module) if not name.startswith('_') and isinstance(getattr(module, name), type)]
        elif item_type == "function":
            return [name for name in dir(module) if callable(getattr(module, name)) and not name.startswith('_')]
        else:
            return [name for name in dir(module) if not name.startswith('_')]
    
    def load_nnModule(self, file_path, name, **kwargs):
        try:
            module = self._load_module(file_path)
            
            if not hasattr(module, name):
                available_classes = self._get_available_items(module, "class")
                raise AttributeError(
                    f"Class '{name}' not found in {file_path}. "
                    f"Available classes: {available_classes}"
                )
            
            target_class = getattr(module, name)

            if not isinstance(target_class, type):
                raise TypeError(f"'{name}' in {file_path} is not a class")
                
            if not issubclass(target_class, torch.nn.Module):
                raise TypeError(
                    f"Class '{name}' in {file_path} must inherit from nn.Module. "
                    f"Current base classes: {[base.__name__ for base in target_class.__bases__]}"
                )

            instance = target_class(**kwargs)
            return instance
        
        except Exception as e:
            raise Exception(f"Error loading model '{name}' from {file_path}: {str(e)}")
    
    def load_dataset(self, file_path, name, **kwargs):
        try:
            module = self._load_module(file_path)
            
            if not hasattr(module, name):
                available_classes = self._get_available_items(module, "class")
                raise AttributeError(
                    f"Class '{name}' not found in {file_path}. "
                    f"Available classes: {available_classes}"
                )
            
            target_class = getattr(module, name)

            if not isinstance(target_class, type):
                raise TypeError(f"'{name}' in {file_path} is not a class")
                
            if not issubclass(target_class, torch.utils.data.Dataset):
                raise TypeError(
                    f"Class '{name}' in {file_path} must inherit from nn.Module. "
                    f"Current base classes: {[base.__name__ for base in target_class.__bases__]}"
                )

            instance = target_class(**kwargs)
            return instance
        
        except Exception as e:
            raise Exception(f"Error loading model '{name}' from {file_path}: {str(e)}")
    
    def load_optimizer_scheduler(self, model_parameters,
                                 optimizer_file, optimizer_class, 
                                 scheduler_file, scheduler_class,
                                 optimizer_params=None, scheduler_params=None):

        if optimizer_params is None:
            optimizer_params = {}
        if scheduler_params is None:
            scheduler_params = {}
        
        try:
            # Load optimizer
            optimizer_module = self._load_module(optimizer_file, "_optimizer")
            
            if not hasattr(optimizer_module, optimizer_class):
                available_classes = self._get_available_items(optimizer_module, "class")
                raise AttributeError(
                    f"Optimizer class '{optimizer_class}' not found in {optimizer_file}. "
                    f"Available classes: {available_classes}"
                )
            
            optimizer_target_class = getattr(optimizer_module, optimizer_class)
            if not isinstance(optimizer_target_class, type):
                raise TypeError(f"'{optimizer_class}' in {optimizer_file} is not a class")

            optimizer_instance = optimizer_target_class(model_parameters, **optimizer_params)
            
            # Load scheduler
            scheduler_module = self._load_module(scheduler_file, "_scheduler")
            
            if not hasattr(scheduler_module, scheduler_class):
                available_classes = self._get_available_items(scheduler_module, "class")
                raise AttributeError(
                    f"Scheduler class '{scheduler_class}' not found in {scheduler_file}. "
                    f"Available classes: {available_classes}"
                )
            
            scheduler_target_class = getattr(scheduler_module, scheduler_class)
            if not isinstance(scheduler_target_class, type):
                raise TypeError(f"'{scheduler_class}' in {scheduler_file} is not a class")
            
            scheduler_instance = scheduler_target_class(optimizer_instance, **scheduler_params)
            
            return optimizer_instance, scheduler_instance
        
        except Exception as e:
            raise Exception(f"Error loading optimizer/scheduler: {str(e)}")
    
    def load_function(self, file_path, name):
        try:
            module = self._load_module(file_path)
            
            if not hasattr(module, name):
                available_functions = self._get_available_items(module, "function")
                raise AttributeError(
                    f"Function '{name}' not found in {file_path}. "
                    f"Available functions: {available_functions}"
                )
            
            target_function = getattr(module, name)
            
            if not callable(target_function):
                raise TypeError(f"'{name}' in {file_path} is not a function")
            
            return target_function
        
        except Exception as e:
            raise Exception(f"Error loading function '{name}' from {file_path}: {str(e)}")
    
    def load_optimizer_only(self, file_path, name, model_parameters, **kwargs):
        try:
            module = self._load_module(file_path, "_optimizer")
            
            if not hasattr(module, name):
                available_classes = self._get_available_items(module, "class")
                raise AttributeError(
                    f"Optimizer class '{name}' not found in {file_path}. "
                    f"Available classes: {available_classes}"
                )
            
            target_class = getattr(module, name)
            if not isinstance(target_class, type):
                raise TypeError(f"'{name}' in {file_path} is not a class")
            
            return target_class(model_parameters, **kwargs)
        
        except Exception as e:
            raise Exception(f"Error loading optimizer '{name}' from {file_path}: {str(e)}")
    
    def load_scheduler_only(self, file_path, name, optimizer, **kwargs):
        try:
            module = self._load_module(file_path, "_scheduler")
            
            if not hasattr(module, name):
                available_classes = self._get_available_items(module, "class")
                raise AttributeError(
                    f"Scheduler class '{name}' not found in {file_path}. "
                    f"Available classes: {available_classes}"
                )
            
            target_class = getattr(module, name)
            if not isinstance(target_class, type):
                raise TypeError(f"'{name}' in {file_path} is not a class")
            
            return target_class(optimizer, **kwargs)
        
        except Exception as e:
            raise Exception(f"Error loading scheduler '{name}' from {file_path}: {str(e)}")


def get_methods_dict(cls_or_instance, include_private=False):
    if inspect.isclass(cls_or_instance):
        instance = cls_or_instance()
    else:
        instance = cls_or_instance
    
    methods_dict = {}
    for name in dir(instance):
        if not include_private and name.startswith('_'):
            continue            
        attr = getattr(instance, name)
        if callable(attr) and not name.startswith('__'):
            methods_dict[name] = attr
    
    return methods_dict