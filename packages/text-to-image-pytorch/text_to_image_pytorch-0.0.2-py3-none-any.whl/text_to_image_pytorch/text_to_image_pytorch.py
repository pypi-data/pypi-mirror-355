import torch
from torch import nn
import torch.nn.functional as F


class TextToImage(nn.Module):
    def __init__(self):
        super().__init__()

    def forward(self, x):
        return x
