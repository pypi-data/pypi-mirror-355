import torch
import inspect
import torchaudio.datasets
import torchvision.datasets
from torch.utils.data import DataLoader
from typing import Optional, Dict, Any, List, Union, Tuple



class Predefined_Dataset:
    """
    A class to fetch and load datasets from torchvision, torchaudio, and torchtext.
    Provides unified access to all PyTorch predefined datasets.
    """
    
    def __init__(self):
        """Initialize the dataset fetcher and discover available datasets."""
        self.torchvision_datasets = self._get_torchvision_datasets()
        self.torchaudio_datasets = self._get_torchaudio_datasets()
        self.all_datasets = self._combine_all_datasets()
    
    def _get_torchvision_datasets(self) -> List[str]:
        """Get available datasets from torchvision.datasets"""
        datasets = []
        for name in dir(torchvision.datasets):
            if not name.startswith('_'):
                attr = getattr(torchvision.datasets, name)
                if (inspect.isclass(attr) and 
                    hasattr(attr, '__init__') and
                    name not in ['DatasetFolder', 'VisionDataset', 'ImageFolder']):
                    datasets.append(name)
        return sorted(datasets)
    
    def _get_torchaudio_datasets(self) -> List[str]:
        """Get available datasets from torchaudio.datasets"""
        datasets = []
        for name in dir(torchaudio.datasets):
            if not name.startswith('_'):
                attr = getattr(torchaudio.datasets, name)
                if inspect.isclass(attr) and hasattr(attr, '__init__'):
                    datasets.append(name)
        return sorted(datasets)
    
    def _combine_all_datasets(self) -> Dict[str, str]:
        """Combine all datasets with their library source"""
        combined = {}
        for dataset in self.torchvision_datasets:
            combined[dataset] = 'torchvision'
        for dataset in self.torchaudio_datasets:
            combined[dataset] = 'torchaudio'
        return combined
    
    def fetch_dataset(self, 
                     dataset_name: str,
                     root: str = "./data",
                     download: bool = True,
                     train: Optional[bool] = None,
                     split: Optional[str] = None,
                     transform: Optional[Any] = None,
                     target_transform: Optional[Any] = None,
                     **kwargs) -> Union[torch.utils.data.Dataset, Tuple]:
        """
        Fetch and load a dataset from any PyTorch dataset library.
        
        Args:
            dataset_name: Name of the dataset to fetch
            root: Root directory for dataset storage
            download: Whether to download the dataset if not found
            train: Whether to load training split (for datasets that support it)
            split: Specific split to load (train/test/valid/etc.)
            transform: Transforms to apply to data
            target_transform: Transforms to apply to targets
            **kwargs: Additional arguments for dataset initialization
            
        Returns:
            Loaded dataset or tuple of datasets
            
        Raises:
            ValueError: If dataset is not found
            RuntimeError: If dataset loading fails
        """
        
        if dataset_name not in self.all_datasets:
            total_count = len(self.all_datasets)
            raise ValueError(
                f"Dataset '{dataset_name}' not found in any PyTorch dataset library. "
                f"Available datasets ({total_count} total):\n"
                f"- Torchvision: {len(self.torchvision_datasets)} datasets\n"
                f"- Torchaudio: {len(self.torchaudio_datasets)} datasets\n"
                f"- Torchtext: {len(self.torchtext_datasets)} datasets\n"
                f"Use list_available_datasets() to see all available datasets."
            )
        
        library = self.all_datasets[dataset_name]
        
        try:
            if library == 'torchvision':
                return self._load_torchvision_dataset(
                    dataset_name, root, download, train, transform, target_transform, **kwargs
                )
            elif library == 'torchaudio':
                return self._load_torchaudio_dataset(
                    dataset_name, root, download, split, **kwargs
                )
        except Exception as e:
            raise RuntimeError(
                f"Failed to load dataset '{dataset_name}' from {library}. "
                f"Error: {e}"
            )
    
    def _load_torchvision_dataset(self, 
                                 dataset_name: str, 
                                 root: str,
                                 download: bool,
                                 train: Optional[bool],
                                 transform: Optional[Any],
                                 target_transform: Optional[Any],
                                 **kwargs):
        """Load a dataset from torchvision.datasets"""
        dataset_class = getattr(torchvision.datasets, dataset_name)
        
        # Prepare arguments
        args = {"root": root, "download": download}
        
        # Add transform arguments if provided
        if transform is not None:
            args["transform"] = transform
        if target_transform is not None:
            args["target_transform"] = target_transform
        
        # Handle train parameter for datasets that support it
        sig = inspect.signature(dataset_class.__init__)
        if 'train' in sig.parameters and train is not None:
            args["train"] = train
        
        # Add additional kwargs
        args.update(kwargs)
        
        return dataset_class(**args)
    
    def _load_torchaudio_dataset(self, 
                                dataset_name: str,
                                root: str,
                                download: bool,
                                split: Optional[str],
                                **kwargs):
        """Load a dataset from torchaudio.datasets"""
        dataset_class = getattr(torchaudio.datasets, dataset_name)
        
        # Prepare arguments
        args = {"root": root, "download": download}
        
        # Handle subset/split parameter
        sig = inspect.signature(dataset_class.__init__)
        if split is not None:
            if 'subset' in sig.parameters:
                args["subset"] = split
            elif 'split' in sig.parameters:
                args["split"] = split
        
        # Add additional kwargs
        args.update(kwargs)
        
        return dataset_class(**args)
    
    def list_available_datasets(self) -> Dict[str, List[str]]:
        """List all available datasets categorized by library"""
        return {
            'torchvision': self.torchvision_datasets,
            'torchaudio': self.torchaudio_datasets,
        }
    
    def search_dataset(self, query: str) -> Dict[str, List[str]]:
        """Search for datasets containing the query string"""
        results = {
            'torchvision': [],
            'torchaudio': [],
        }
        
        query_lower = query.lower()
        
        for dataset in self.torchvision_datasets:
            if query_lower in dataset.lower():
                results['torchvision'].append(dataset)
        
        for dataset in self.torchaudio_datasets:
            if query_lower in dataset.lower():
                results['torchaudio'].append(dataset)
        
        return results
    
    def get_dataset_info(self, dataset_name: str) -> Dict[str, Any]:
        """Get detailed information about a specific dataset"""
        if dataset_name not in self.all_datasets:
            return {'found': False, 'error': f"Dataset '{dataset_name}' not found"}
        
        library = self.all_datasets[dataset_name]
        
        if library == 'torchvision':
            dataset_class = getattr(torchvision.datasets, dataset_name)
        elif library == 'torchaudio':
            dataset_class = getattr(torchaudio.datasets, dataset_name)
        
        # Get constructor parameters
        try:
            sig = inspect.signature(dataset_class.__init__ if library != 'torchtext' else dataset_class)
            parameters = list(sig.parameters.keys())
            if library != 'torchtext' and 'self' in parameters:
                parameters.remove('self')
        except:
            parameters = []
        
        # Get docstring
        docstring = dataset_class.__doc__ or "No documentation available"
        
        return {
            'found': True,
            'name': dataset_name,
            'library': library,
            'class': dataset_class,
            'parameters': parameters,
            'docstring': docstring.split('\n')[0] if docstring else "No description",
            'supports_download': 'download' in parameters,
            'supports_train_split': 'train' in parameters,
            'supports_custom_split': any(param in parameters for param in ['split', 'subset'])
        }
    
    def create_dataloader(self, 
                         dataset: torch.utils.data.Dataset,
                         batch_size: int = 32,
                         shuffle: bool = True,
                         num_workers: int = 0,
                         **kwargs) -> DataLoader:
        """Create a DataLoader for the given dataset"""
        return DataLoader(
            dataset, 
            batch_size=batch_size, 
            shuffle=shuffle, 
            num_workers=num_workers,
            **kwargs
        )

    
    def get_popular_datasets(self) -> Dict[str, List[str]]:
        """Get a curated list of popular datasets from each library"""
        return {
            'torchvision': [
                'MNIST', 'CIFAR10', 'CIFAR100', 'ImageNet', 'FashionMNIST', 
                'SVHN', 'STL10', 'CelebA', 'CocoDetection'
            ],
            'torchaudio': [
                'SPEECHCOMMANDS', 'COMMONVOICE', 'LIBRISPEECH', 'VCTK_092', 
                'YESNO', 'GTZAN'
            ]
        }