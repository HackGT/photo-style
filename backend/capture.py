import os
import subprocess
import sys
import logging
import requests

import gphoto2 as gp
import cv2
import time

from PIL import Image
from io import BytesIO


if __name__ == "__main__":
    gp.check_result(gp.use_python_logging())
    camera = gp.check_result(gp.gp_camera_new())
    gp.check_result(gp.gp_camera_init(camera))
    print('Capturing image')

    while True:
        file_path = gp.check_result(gp.gp_camera_capture(camera, gp.GP_CAPTURE_IMAGE))
        print('Camera file path: {0}/{1}'.format(file_path.folder, file_path.name))
        camera_file = gp.check_result(gp.gp_camera_file_get(camera, file_path.folder, file_path.name, gp.GP_FILE_TYPE_NORMAL))
        im = Image.open(BytesIO(camera_file.get_data_and_size()))
        im = im.resize((int(im.size[0] / 3), int(im.size[1] / 3)), Image.LANCZOS)

        #get file stream
        image_stream = BytesIO()
        im.save(image_stream, 'JPEG')
        image_stream.seek(0)

        s = time.time()
        r = requests.post('http://localhost:9000/convert', files={'file': image_stream})
        print(time.time() - s)

        out = Image.open(BytesIO(r.content))
        out.save('temp.jpg')
        cv2.imshow('capture', cv2.imread('temp.jpg'))


    gp.check_result(gp.gp_camera_exit(camera))
