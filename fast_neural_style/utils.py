import torch
import os
import base64
import requests
import re
from PIL import Image
from io import BytesIO
from torch.autograd import Variable


def load_image(filename, size=None, scale=None):
    img = Image.open(filename)
    if size is not None:
        img = img.resize((size, size), Image.ANTIALIAS)
    elif scale is not None:
        img = img.resize((int(img.size[0] / scale), int(img.size[1] / scale)), Image.ANTIALIAS)
    return img


def load_image_from_url(url):
    #stream from url directly into pil image, without buffering
    image = Image.open(requests.get(url, stream=True).raw)
    return image


def load_from_base64(base64_string):
    data = re.sub('^data:image/.+;base64,', '', base64_string)
    return Image.open(BytesIO(base64.b64decode(data)))
   

def get_image_stream(output_tensor):
    image = get_image(output_tensor)
    io_stream = BytesIO()
    image.save(io_stream, 'PNG')
    io_stream.seek(0)
    return io_stream


def get_image(tensor):
    #TODO: cloning the tensor is cheap on gpu but could fail on cpu
    #TODO: check memory performance
    image = tensor.clone().clamp(0, 255).numpy()
    image = image.transpose(1, 2, 0).astype("uint8")
    return Image.fromarray(image)


def save_image(filename, data):
    img = data.clone().clamp(0, 255).numpy()
    img = img.transpose(1, 2, 0).astype("uint8")
    img = Image.fromarray(img)
    img.save(filename)


def get_paths(source, recurse=False):
    paths = []
    names = []
    for _, _, filenames in os.walk(source):
        for i, f in enumerate(filenames):
            fullpath = os.path.join(source, f)
            names.append(f)
            paths.append(fullpath)
        if not recurse:
            break

    return paths, names


def gram_matrix(y):
    (b, ch, h, w) = y.size()
    features = y.view(b, ch, w * h)
    features_t = features.transpose(1, 2)
    gram = features.bmm(features_t) / (ch * h * w)
    return gram


def normalize_batch(batch):
    # normalize using imagenet mean and std
    mean = batch.data.new(batch.data.size())
    std = batch.data.new(batch.data.size())
    mean[:, 0, :, :] = 0.485
    mean[:, 1, :, :] = 0.456
    mean[:, 2, :, :] = 0.406
    std[:, 0, :, :] = 0.229
    std[:, 1, :, :] = 0.224
    std[:, 2, :, :] = 0.225
    batch = torch.div(batch, 255.0)
    batch -= Variable(mean)
    batch = batch / Variable(std)
    return batch

def is_cuda(model):
    # hack, but an official hack
    return next(model.parameters()).is_cuda
