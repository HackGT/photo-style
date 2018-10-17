import argparse
import torch
import requests
import re
import random
from flask import Flask, request, send_file, jsonify, send_from_directory
from flask_cors import CORS, cross_origin
from PIL import Image
from io import BytesIO
import numpy as np
import os
import json
import base64

# from fast_neural_style.forward import forward_pass
import DetectronPytorch.tools._init_paths
from fast_neural_style.transformer_net import TransformerNet
from DetectronPytorch.tools.wrapped_model import WrappedDetectron, union_masks, apply_binary_mask
from joint_forward import segment_and_style
from fast_neural_style.utils import get_image_stream, load_from_base64

app = Flask(__name__)
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'

models = []
model_names = [
    'starry night',
    'starry-er night',
    'mosaic',
    'sunset'
]
model_paths = [
    'models/starry_night/starry01.model',
    'models/starry_night/starry02.model',
    'models/mosaic/mosaic_0.4.1.model',
    'models/scream/scream.model'
]
model_map = {}
detectron = WrappedDetectron('./DetectronPytorch')

@app.route('/')
def root():
    return send_from_directory('', 'test_index.html')


@app.route('/convert', methods=['POST', 'GET'])
def convert():
    im = Image.open(request.files['file'])
    im = im.resize((int(im.size[0] / 1), int(im.size[1] / 1)), Image.LANCZOS)
    print(im)
    model_name = random.choice(model_names)
    mask, scored_masks, styled_images = segment_and_style(models, detectron, im)

    numpy_image = np.array(im)
    if len(scored_masks) > 0:
        mask = ~union_masks(scored_masks)
        numpy_image, _, _ = apply_binary_mask(numpy_image, random.choice(styled_images), mask)
    else:
        numpy_image = random.choice(styled_images)

    image = Image.fromarray(numpy_image)
    io_stream = BytesIO()
    image.save(io_stream, 'PNG')
    io_stream.seek(0)
    return send_file(io_stream, mimetype='image/PNG')

@app.route('/convert_encoded', methods=['POST'])
@cross_origin()
def convert_encoded():
    request_data = request.get_json(force=True)
    im = load_from_base64(request_data['image'])

    print(im)

    model_name = random.choice(model_names)
    mask, scored_masks, styled_images = segment_and_style(models, detectron, im)
    print("Found {} people".format(len(scored_masks)))

    numpy_image = np.array(im)

    filter_payload = []
    for image in styled_images:
        i = Image.fromarray(image)
        buffered = BytesIO()
        i.save(buffered, format="JPEG")
        filter_payload.append(base64.b64encode(buffered.getvalue()).decode('ascii'))

    return jsonify({'filters' : filter_payload, 'mask' : mask.tolist()})

def load_style_model(path_to_model):
    model = TransformerNet()
    model.load_state_dict(torch.load(path_to_model))
    return model

if __name__ == '__main__':
    for model_name, model_path in zip(model_names, model_paths):
        # models[model_name] = load_style_model(model_paths
        model = load_style_model(model_path)
        models.append(model)
        model_map[model_name] = model

    print(model_map)
    app.run(debug=False, port=8080, host='0.0.0.0')
