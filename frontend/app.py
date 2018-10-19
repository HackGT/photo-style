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

from dotenv import load_dotenv
load_dotenv()

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
    im = im.resize((int(im.size[0] / 3), int(im.size[1] / 3)), Image.LANCZOS)

    #get file stream
    image_stream = BytesIO()
    im.save(image_stream, 'JPEG')
    # image_stream.seek(0)
    
    image_base64 = base64.b64encode(image_stream.getvalue()).decode('ascii')
    # return jsonify({'image': ""}) # Testing
    return jsonify({'image': image_base64})

    # gp.check_result(gp.gp_camera_exit(camera))

@app.route('/get_email', methods=['POST'])
def get_email():
    request_data = request.get_json(force=True)
    id = request_data['id']
    queryStr = "{" + \
        'user(id: "{}") {{'.format(id) + \
            "email" + \
        "}" + \
    "}"
    data = { "query": queryStr }
    headers = {'Authorization': 'Basic ' + os.environ['REGISTRATION_API_KEY']}
    print(data)
    print(headers)
    res = requests.post(os.environ['REGISTRATION_URL'], json=data, headers=headers)
    print(res.json())
    email = res.json()['data']['user']['email']
    return jsonify({'email': email}) # forward to frontend

@app.route('/')
def home():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
