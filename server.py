import argparse
import torch
import requests
from io import BytesIO
from flask import Flask, request, send_file
from fast_neural_style.forward import forward_pass
from fast_neural_style.transformer_net import TransformerNet
from fast_neural_style.utils import load_image_from_url, get_image

app = Flask(__name__)

#TODO: read models and options from a real config file
model_cache = {}
model_paths = {
    'psych01' : './models/psych01/psych01.model',
    'psych02' : './models/psych02/psych02.model',
    'water01' : './models/water01/water01.model'
}



@app.route('/convert')
def convert():
    image_url = request.args.get('image_url')
    style = request.args.get('style')
    image = load_image_from_url(image_url)
    if style is None:
        style = 'psych02'
    out_tensor = forward_pass(model_cache[style], image)
    image = get_image(out_tensor)
    io_stream = BytesIO()
    image.save(io_stream, 'JPEG')
    io_stream.seek(0)

    return send_file(io_stream, mimetype='image/jpeg')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Launch a style transfer server")
    parser.add_argument('--gpu', dest='cuda', action='store_true', 
            help='Use gpu models to process requests')
    parser.add_argument('--cpu', dest='cuda', action='store_false', 
            help='Use cpu models to process requests')
    parser.set_defaults(cuda=True)

    args = parser.parse_args()

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

    app.run(debug=False, host='0.0.0.0')

