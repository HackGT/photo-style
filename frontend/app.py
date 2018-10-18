from flask import Flask, request, url_for, render_template, jsonify
import os
import subprocess
import sys
import logging
import requests

import base64

import gphoto2 as gp

from PIL import Image
from io import BytesIO

app = Flask(__name__)

@app.route('/capture', methods=['POST'])
def take_photo():
    gp.check_result(gp.use_python_logging())
    camera = gp.check_result(gp.gp_camera_new())
    gp.check_result(gp.gp_camera_init(camera))
    print('Capturing image')

    file_path = gp.check_result(gp.gp_camera_capture(camera, gp.GP_CAPTURE_IMAGE))
    print('Camera file path: {0}/{1}'.format(file_path.folder, file_path.name))
    camera_file = gp.check_result(gp.gp_camera_file_get(camera, file_path.folder, file_path.name, gp.GP_FILE_TYPE_NORMAL))
    im = Image.open(BytesIO(camera_file.get_data_and_size()))
    im = im.resize((int(im.size[0] / 8), int(im.size[1] / 8)), Image.BILINEAR)

    #get file stream
    image_stream = BytesIO()
    im.save(image_stream, 'JPEG')
    # image_stream.seek(0)
    image_base64 = base64.b64encode(image_stream.getvalue()).decode('ascii')
    return jsonify({'image': image_base64})

    # gp.check_result(gp.gp_camera_exit(camera))

@app.route('/')
def home():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
