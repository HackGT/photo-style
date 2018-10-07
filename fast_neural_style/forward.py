import argparse
import os
import sys
import time

import numpy as np
import torch
from torch.autograd import Variable
from torchvision import transforms

from . import utils
from .transformer_net import TransformerNet
from .vgg import Vgg16


def forward_pass(model, image, device, pipeline=None):
    if pipeline is None:
        pipeline = transforms.Compose([
                        transforms.ToTensor(),
                        transforms.Lambda(lambda x: x.mul(255))
                    ])

    batch_tensor = pipeline(image).unsqueeze(0).to(device)

    # if cuda and not utils.is_cuda(model):
        # raise Exception("Cuda specified but provided model is not cuda!")
    model.to(device)
    model.eval()
    with torch.no_grad():
        output_tensor = model(batch_tensor).data[0]
    
    output_tensor = output_tensor.cpu()

    return output_tensor

