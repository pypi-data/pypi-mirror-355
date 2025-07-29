import torch.nn as nn
from torch.optim import Optimizer
from torch.utils.data import Dataset
from torch.optim.lr_scheduler import _LRScheduler



class TrainingDataset(Dataset):
    def __init__(self):
        super().__init__()
        """
        Your Initialization Code for Dataset
        """
    
    def __len__(self):
        """
        Total length of data, i.e. Total number of samples
        """
        return
    
    def __getitem__(self, index):
        """
        return (data_sample, label) 
        """
        return
    
    
class TrainingModel(nn.Module):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        """
        Your Initialization code for model
        """
    
    def forward(self, INPUT):
        """
        Your Model Logic
        """
        return
    

class TrainingLossFunction(nn.Module):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        """
        Your Initialization code for Loss Function
        """
        
    def forward(self, OUTPUT, LABELS):
        """
        Your Loss Function Logic
        return (softmax_output, loss_value)
        """
        return
    

class TrainingOptimizer(Optimizer):
    def __init__(self, params, defaults):
        super().__init__(params, defaults)
        """
        Your Initialization code for optimizer
        """
    
    def step(self, closure=None):
        """
        Your Logic for optimizer
        return (loss_value)
        """
        return 
    
class TrainingScheduler(_LRScheduler):
    def __init__(self, optimizer, last_epoch = -1):
        super().__init__(optimizer, last_epoch)
        """
        Your initialization code for scheduler
        """
    
    def get_lr(self):
        """
        Return the current learning rate
        """
        return super().get_lr()
    


def classic_minibatch_logic(minibatch, model, loss_fn, optimizer, device):
        data, label = minibatch
        data, label = data.squeeze(1).to(device), label.to(device)
        optimizer.zero_grad()
        output = model(data)
        loss, out = loss_fn(output, label)
        loss.backward()
        optimizer.step()
        return out, loss


CONFIG_JSON = {
    "experiment_name": "",

    "dataset":{
        "name/codefile": "File Path containing Dataset Code / Name of Dataset",
        "class_name": "TrainingDataset",
        "parameters":{
            
        }
    },

    "architecture":{
        "name/codefile": "File Path containing Architecture Code / Name of Architecture",
        "class_name": "TrainingModel",
        "parameters":{

        }
    },

    "loss_function":{
        "name/codefile": "File Path containing Loss Function Code / Name of Loss Function",
        "class_name": "TrainingLossFunction",
        "train": "either true / flase",
        "parameters":{

        }
    },

    "optimizer":{
        "name/codefile": "File Path containing optimizer Code / Name of optimizer",
        "class_name": "TrainingOptimizer",
        "parameters":{

        }
    },

    "scheduler":{
        "name/codefile": "File Path containing scheduler Code / Name of scheduler",
        "class_name": "TrainingScheduler",
        "parameters":{

        }
    },

    "minibatch_logic": {
        "name/codefile": "File Path containing minibatch logic code / Name of minibatch logic"
    },

    "training":{
        "epochs": 120,
        "batchsize": 48,
        "num_workers": 2,
        "metric": "accuracy",
        "mgpu": "either true / false",
        "gpu": 1,
        "num_gpus": 3,
        "log_minibatchstats_after": 10,
        "log_gradients_after": 100
    }
}