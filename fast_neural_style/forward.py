import argparse
import os
import sys
import time

import numpy as np
import torch
from torch.autograd import Variable
from torch.optim import Adam
from torch.utils.data import DataLoader, Dataset
from torchvision import datasets
from torchvision import transforms

from . import utils
from .transformer_net import TransformerNet
from .vgg import Vgg16


def forward_pass(model, image, cuda=True, pipeline=None):
    if pipeline is None:
        pipeline = transforms.Compose([
                        transforms.ToTensor(),
                        transforms.Lambda(lambda x: x.mul(255))
                    ])

    batch_tensor = pipeline(image).unsqueeze(0)

    if cuda and not utils.is_cuda(model):
        raise Exception("Cuda specified but provided model is not cuda!")
    
    model.eval() 
    
    if cuda:
        batch_tensor = batch_tensor.cuda()

    batch_variable = Variable(batch_tensor, volatile=True)
    
    output_tensor = model(batch_variable).data[0]

    if cuda:
        output_tensor = output_tensor.cpu()

    return output_tensor

