import argparse
import torch
import requests
import re
from flask import Flask, request, send_file, jsonify
from flask_cors import CORS, cross_origin
from fast_neural_style.forward import forward_pass
from fast_neural_style.transformer_net import TransformerNet
from fast_neural_style.utils import load_image_from_url, get_image, \
                                    load_from_base64, get_image_stream, \
                                    get_gcloud_url
import os
from twilio.rest import Client

app = Flask(__name__)
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'

#TODO: read models and options from a real config file
model_cache = {}
model_paths = {
    'psych01' : './models/psych01/psych01.model',
    'psych02' : './models/psych02/psych02.model',
    'psych03' : './models/psych03/psych03.model',
    'water01' : './models/water01/water01.model',
    'mosaic01': './models/mosaic01/mosaic01.model',
    'neon01'  : './models/neon01/neon01.model',
    'eagle01' : './models/eagle01_tuned/eagle01_tuned.model',
    'album01' : './models/album01/album01.model',
    'cube01'  : './models/cube01/cube01.model',
    'cheetos01':'./models/cheetos01/cheetos01.model'
}
account = os.environ['TWILIO_ACCOUNT']
token = os.environ["TWILIO_TOKEN"]
client = Client(account, token)

@app.route('/send-mms', methods=['POST'])
@cross_origin()
def send_mms():
    client.messages.create(
        to=request.get_json(force=True)['phone'],
        messaging_service_sid=os.environ["TWILIO_SERVICE"],
        body="",
        media_url=request.get_json(force=True)['url']
    )
    return jsonify()

@app.route('/convert_encoded', methods=['POST'])
@cross_origin()
def convert_encoded():
    request_data = request.get_json(force=True)

    if 'style' in request_data:
        style = request_data['style']
    else:
        style = 'psych02'

    image = load_from_base64(request_data['image_url'])
    # resize max of 1280 x 720 while keeping aspect ratio
    image.thumbnail((1280, 1280))
    out_tensor = forward_pass(model_cache[style], image, app.config['cuda'])
    return jsonify({
        "url": get_gcloud_url(get_image_stream(out_tensor))
    })


@app.route('/convert')
@cross_origin()
def convert():
    image_url = request.args.get('image_url')
    style = request.args.get('style')
    # splits = re.split(r'&?(image_url|style)=', request.full_path)
    # style = splits[-1]
    # image_url = splits[2]
    image = load_image_from_url(image_url)
    if style is None:
        style = 'psych02'
    image.thumbnail((1280, 1280))
    out_tensor = forward_pass(model_cache[style], image, app.config['cuda'])
    # torch keeps a cache of memory allocated on gpu
    # uncomment this to free gpu memory immediately after each conversion
    # will pay the cost of allocating each time!
    # torch.cuda.empty_cache()
    return jsonify({
        "url": get_gcloud_url(get_image_stream(out_tensor))
    })

@app.route('/styles')
@cross_origin()
def list_styles():
    return jsonify({
        'styles': list(model_paths.keys())
    })

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Launch a style transfer server")
    parser.add_argument('--gpu', dest='cuda', action='store_true',
            help='Use gpu models to process requests')
    parser.add_argument('--cpu', dest='cuda', action='store_false',
            help='Use cpu models to process requests')
    parser.set_defaults(cuda=True)

    args = parser.parse_args()

    app.config['cuda'] = args.cuda
    # preload models
    for name, path in model_paths.items():
        model = TransformerNet()
        model.load_state_dict(torch.load(path))
        if args.cuda:
            model.cuda()
        else:
            model.cpu()
        model.eval()
        model_cache[name] = model
        # hack to warm up the gpu
        #TODO: investigate pinning cuda buffers to do this properly
        # dummy = torch.randn((1, 3, 1080, 1920))
        # if args.cuda:
            # dummy = dummy.cuda()
        # model(dummy)
    app.run(debug=False, host='0.0.0.0', port=8080)

