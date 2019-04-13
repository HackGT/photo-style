import argparse
import torch
import requests
import re
import random
from flask import Flask, request, send_file, jsonify, send_from_directory
from flask_cors import CORS, cross_origin
import sendgrid
import os
from sendgrid.helpers.mail import *

from google.cloud import storage
from dotenv import load_dotenv
load_dotenv()

from PIL import Image
from io import BytesIO
import numpy as np
import os
import json
import base64

import skimage

# from fast_neural_style.forward import forward_pass
import DetectronPytorch.tools._init_paths
from fast_neural_style.transformer_net import TransformerNet
from DetectronPytorch.tools.wrapped_model import WrappedDetectron, union_masks, apply_binary_mask
from joint_forward import segment_and_style
from fast_neural_style.utils import get_image_stream, load_from_base64

import torch.nn.functional as F
import torch

EVENT_NAME = "Catalyst"
app = Flask(__name__)
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'
models = []
model_names = [
    'starry night',
    # 'starry-er night',
    'mosaic',
    'sunset',
    'green',
    'cube'
]
model_paths = [
    'models/starry_night/starry01.model',
    # 'models/starry_night/starry02.model',
    'models/mosaic/mosaic_0.4.1.model',
    'models/scream/scream.model',
    'models/med/med.model',
    'models/cube01/cube01_0.4.1.model'
]
model_map = {}
detectron = WrappedDetectron('./DetectronPytorch')
image_cache = {}

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

    print('Input Image: {}'.format(im.size))
    model_name = random.choice(model_names)
    mask, scored_masks, styled_images = segment_and_style(models, detectron, im)
    numpy_image = np.array(im)
    print("Found {} people".format(len(scored_masks)))

    image_cache['source_im'] = numpy_image.copy()
    image_cache['scored_masks'] = [m.copy() for m in scored_masks]
    image_cache['styled_images'] = [i.copy() for i in styled_images]


    filter_payload = []
    for image in styled_images:
        i = Image.fromarray(image)
        i = i.resize((int(i.size[0] / 3), int(i.size[1] / 3)))
        # i.thumbnail((256, 256), Image.ANTIALIAS)
        print(i.size)
        buffered = BytesIO()
        i.save(buffered, format="JPEG")
        filter_payload.append(base64.b64encode(buffered.getvalue()).decode('ascii'))

    resized_mask = F.max_pool2d(torch.FloatTensor(mask).unsqueeze(dim=0), (3, 3), stride=3)
    resized_mask = resized_mask.squeeze().numpy().astype(int)

    im = im.resize((int(im.size[0] / 3), int(im.size[1] / 3)))
    buffered = BytesIO()
    im.save(buffered, format="JPEG")
    source = base64.b64encode(buffered.getvalue()).decode('ascii')


    return jsonify({'filters' : filter_payload, 'mask' : resized_mask.tolist(), 'source' : source})

@app.route('/send_email', methods=['POST'])
@cross_origin()
def prepare_final():
    request_data = request.get_json(force=True)
    print(request_data)
    email = request_data['email']
    mix_info = request_data['mixInfo']

    # EDIT HERE
    # final_filename = "cheetos01.png" # high_res_mix(mix_info) # fill in this
    out = image_cache['source_im']
    for mask_ix, filter_ix in mix_info.items():
        mask_ix = int(mask_ix)
        mask = image_cache['scored_masks'][mask_ix]
        mask = (mask != 0)
        out, _, _ = apply_binary_mask(out, image_cache['styled_images'][filter_ix - 1], mask)

    out_image = Image.fromarray(out)
    out_image.save('hello.jpg')

    # final_res should be in file_name - rename to some unique identifier PER photo
    # bucket initialized from console
    bucket_name = os.environ['CLOUD_BUCKET']
    object_name = ''.join(random.choice('abcdefghijklmnopqrstuvwxyz0123456789') for i in range(16)) + ".jpg"
    client = storage.Client()
    bucket = client.get_bucket(bucket_name)
    blob = bucket.blob(object_name)

    #crop the bottom edge to improve quality, slightly
    out_image = out_image.crop((0, 0, 2000, 1293))

    stream = BytesIO()
    out_image.save(stream, format="JPEG")
    stream.seek(0)

    blob.upload_from_file(stream, content_type="image/jpg", client=client)
    blob.make_public()
    gcloud_link = "http://storage.googleapis.com/{}/{}".format(bucket_name, object_name)
    print(gcloud_link)
    sg = sendgrid.SendGridAPIClient(os.environ['SENDGRID_API_KEY'])
    from_email = os.environ["FROM_EMAIL"]
    to_email = email
    subject = "{} - Photobooth Link".format(EVENT_NAME)
    content = '<a href="{}">Here</a> is a link to your photo. Have a nice day!'.format(gcloud_link)
    mail = Mail(from_email=from_email, to_emails=to_email, subject=subject, html_content=content)
    response = sg.client.mail.send.post(request_body=mail.get())

    return jsonify(success=True)

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

    app.run(debug=False, port=8080, host='0.0.0.0')
