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


def check_paths(args):
    try:
        if not os.path.exists(args.save_model_dir):
            os.makedirs(args.save_model_dir)
        if args.checkpoint_model_dir is not None and not (os.path.exists(args.checkpoint_model_dir)):
            os.makedirs(args.checkpoint_model_dir)
    except OSError as e:
        print(e)
        sys.exit(1)

def get_paths(source):
    paths = []
    names = []
    for _, _, filenames in os.walk(source):
        for i, f in enumerate(filenames):
            fullpath = os.path.join(source, f)
            names.append(f)
            paths.append(fullpath)

    return paths, names


def forward(args):
    paths, filenames = get_paths(args.content_dir)
    images = []

    for path in paths:
        images.append(utils.load_image(path))

    content_transform = transforms.Compose([
        transforms.ToTensor(),
        transforms.Lambda(lambda x: x.mul(255))
    ])

    # init model
    model = TransformerNet()
    model.load_state_dict(torch.load(args.model))

    model.eval()

    if args.cuda:
        model.cuda()

     

    # single batch processing for now (1 frame at a time)
    for image, filename in zip(images, filenames):
        print("Processing {}".format(filename))
        # wrap tensor with a fake batch dimension
        content_tensor = content_transform(image).unsqueeze(0)

        # should always use cuda
        if args.cuda:
            content_tensor = content_tensor.cuda()
        
        content_variable = Variable(content_tensor, volatile = True)
        
         
        # run forward pass of model
        out_tensor = model(content_variable).data[0]

        # move tensor from gpu to cpu before writing out
        if args.cuda:
            out_tensor = out_tensor.cpu()

        utils.save_image(os.path.join(args.output_dir, filename), out_tensor)
   

if __name__ == "__main__":
    arg_parser = argparse.ArgumentParser(description="batch style transfer")

    arg_parser.add_argument("--content-dir", type=str, required=True,
                                 help="path to directory containing images you want to stylize")
    # arg_parser.add_argument("--content-scale", type=float, default=None,
                                 # help="factor for scaling down the content image")
    arg_parser.add_argument("--output-dir", type=str, required=True,
                                 help="path for saving the output images")
    arg_parser.add_argument("--model", type=str, required=True,
                                 help="saved model to be used for stylizing the images")
    arg_parser.add_argument("--cuda", type=int, required=True,
                                 help="set it to 1 for running on GPU, 0 for CPU")
    
    args = arg_parser.parse_args()

    if args.cuda and not torch.cuda.is_available():
        print("ERROR: cuda is not available, try running on CPU")
        sys.exit(1)
    
    forward(args) 


