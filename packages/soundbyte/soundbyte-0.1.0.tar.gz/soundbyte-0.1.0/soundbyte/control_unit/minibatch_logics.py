import torch
import torch.nn.functional as F

class Predefined_MBLogics:

    def supervised_classification_train(self, minibatch, model, loss_fn, optimizer, device):
        data, label = minibatch
        data, label = data.squeeze(1).to(device), label.to(device)
        optimizer.zero_grad()
        output = model(data)
        loss, out = loss_fn(output, label)
        loss.backward()
        optimizer.step()
        return out, loss
    
    def supervised_classification_eval(self, minibatch, model, loss_fn, device):
        data, label = minibatch
        data, label = data.squeeze(1).to(device), label.to(device)
        output = model(data)
        loss, out = loss_fn(output, label)
        return out, loss
    
    def multiply(self, a,b):
        return a*b