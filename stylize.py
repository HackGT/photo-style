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

from fast_neural_style import utils
from fast_neural_style.transformer_net import TransformerNet
from fast_neural_style.vgg import Vgg16
from fast_neural_style.forward import forward_pass


def forward(args):
    paths, filenames = utils.get_paths(args.content_dir)
    images = []

    for path in paths:
        images.append(utils.load_image(path))

    # init model
    model = TransformerNet()
    model.load_state_dict(torch.load(args.model))
    model.eval()
    if args.cuda:
        model.cuda()

    # single batch processing for now (1 frame at a time)
    for image, filename in zip(images, filenames):
        print("Processing {}".format(filename))
        out_tensor = forward_pass(model, image, cuda = (args.cuda == 1))
        utils.save_image(os.path.join(args.output_dir, filename), out_tensor)


if __name__ == "__main__":
    arg_parser = argparse.ArgumentParser(
            description="Script to run style transfer on batches of images")

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


