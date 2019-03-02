from flask import Flask, request, url_for, render_template, jsonify
from flask_socketio import SocketIO
import os
import subprocess
import sys
import logging
import requests
import time

import base64

import gphoto2 as gp
import json

from PIL import Image
from io import BytesIO

from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)
socketio = SocketIO(app)

import threading

# Quick thread for listening
stopevent = None
thread = None
camera = None

@app.route('/capture', methods=['POST'])
def take_photo():
    # gp.check_result(gp.use_python_logging())
    # camera = gp.check_result(gp.gp_camera_new())
    # gp.check_result(gp.gp_camera_init(camera))
    # print('Capturing image')
    global camera
    print(camera)
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
    print("getting email")
    queryStr = "{" + \
        'user(id: "{}") {{'.format(id) + \
            "email" + \
        "}" + \
    "}"
    data = { "query": queryStr }
    headers = {'Authorization': 'Basic ' + os.environ['REGISTRATION_API_KEY']}
    res = requests.post(os.environ['REGISTRATION_URL'], json=data, headers=headers)
    print(res.json())
    email = res.json()['data']['user']['email']
    print(email)
    return jsonify({'email': email}) # forward to frontend

@app.route('/confirm_points', methods=['POST'])
def confirm_points():
    request_data = request.get_json(force=True)
    id = request_data['id']
    queryStr = "{" + \
        'check_in(user: "{}", tag: "misc_photobooth") {{'.format(id) + \
        "}" + \
    "}"
    data = { "mutation": queryStr }
    headers = {'Authorization': 'Basic ' + os.environ['CHECKIN_API_KEY']}
    res = requests.post(os.environ['CHECKIN_URL'], json=data, headers=headers) # something
    return jsonify({'success': True})

@app.route('/')
def home():
    return render_template('index.html')

def wait_for_camera():
    # wait code
    global camera
    gp.check_result(gp.use_python_logging())
    camera = gp.check_result(gp.gp_camera_new())
    gp.check_result(gp.gp_camera_init(camera))
    print('Waiting for camera capture...')
    while True:
        event_type, data = gp.check_result(gp.gp_camera_wait_for_event(camera, gp.GP_EVENT_FILE_ADDED))
        if event_type == gp.GP_EVENT_FILE_ADDED:
            file_path = data
            camera_file = gp.check_result(gp.gp_camera_file_get(camera, file_path.folder, file_path.name, gp.GP_FILE_TYPE_NORMAL))
            print(camera_file)
            im = Image.open(BytesIO(camera_file.get_data_and_size()))
            im = im.resize((int(im.size[0] / 3), int(im.size[1] / 3)), Image.LANCZOS)

            #get file stream
            image_stream = BytesIO()
            im.save(image_stream, 'JPEG')
            # image_stream.seek(0)
            
            image_base64 = base64.b64encode(image_stream.getvalue()).decode('ascii')
            # return jsonify({'image': ""}) # Testing
            socketio.emit('photo-taken', json.dumps({"image": image_base64}));    
        time.sleep(0.1)
    return

@app.route("/ready", methods=['POST'])
def start():
    global stopevent, thread
    if thread is not None:
        return jsonify({'sucess': True, 'message': "thread already exists"})
    threading.Thread(target=wait_for_camera).start()
    # stopevent = threading.Event()
    # thread = LoopThread(1, stopevent) #what can I change here?
    # thread.start() # how do I change the function variable name everytime?
    return jsonify({'success': True, 'message': "camera listen started"})

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
    # app.run(host='0.0.0.0', debug=True)

