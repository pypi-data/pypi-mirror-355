import torch
import torch.nn.functional as F



class Calculator:
    def accuracy(self, softmax_output, labels):
        labels = labels.to(softmax_output.device)

        with torch.no_grad():
            predicted_classes = torch.argmax(softmax_output, dim=1)
            correct_predictions = (predicted_classes == labels).sum().item()
            total_predictions = labels.size(0)
            accuracy_percentage = (correct_predictions / total_predictions) * 100.0        
        return torch.tensor(accuracy_percentage)