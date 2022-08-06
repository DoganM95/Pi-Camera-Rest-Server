from __future__ import print_function
from datetime import datetime
from os import popen, environ
import sys
from unittest import IsolatedAsyncioTestCase
from flask import Flask, request, Response, jsonify, redirect
from flasgger import Swagger
from types import SimpleNamespace as Namespace
import json
from time import sleep


# https://picamera.readthedocs.io/en/release-1.13/index.html
from picamera import PiCamera


template = {
    "securityDefinitions": {"Bearer": {"type": "apiKey", "name": "Authorization", "in": "header"}},
    "swagger": "2.0",
    "info": {
        "title": "Pi Camera Rest Server",
        "description": "Control Raspberry Pi camera using http requests. Files are saved locally on the SD..",
        "contact": {
            "name": "DoganM95",
            "url": "github.com/DoganM95",
        },
        "license": {"name": "Apache 2.0", "url": "https://www.apache.org/licenses/LICENSE-2.0.html"},
        "version": "0.0.1",
    },
    "schemes": ["http", "https"],
    "consumes": [
        "application/json",
    ],
    "produces": [
        "application/json",
    ],
}

app = Flask(__name__)
swagger = Swagger(app, template=template)


@app.route("/")
def redirectRootToDocs():
    return redirect("/apidocs", code=302)


@app.route("/capture/picture", methods=["POST"])
def post_capture_picture():
    """Capture a picture
    This is using docstrings for specifications.
    ---
    parameters:
      - name: resolution
        in: query
        required: false
        default: 1920x1080
        schema:
          type: string
        enum: ['2592x1944', '1920x1080', '1296x972', '1296x730', '640x480' ]
        description:
          2592x1944 max 15 fps, 1920x1080 max 30 fps, 1296x972 max 42 fps, 1296x730 max 49 fps, 640x480 max 90 fps
      - name: useVideoPort
        in: query
        required: false
        default: False
        schema:
          type: boolean
        description:
          Set true to use video port to capture images. Quality is inferior but fps is higher, which results in less blurry images, especially on movement.
      - name: contrast
        in: query
        required: false
        default: 0
        schema:
          type: integer
        description:
          Value between -100 and 100.
      - name: led
        in: query
        required: false
        default: True
        schema:
          type: boolean
      - name: fileType
        in: query
        required: false
        default: 'jpeg'
        schema:
          type: string
        enum: ['jpeg', 'png', 'gif', 'bmp', 'yuv', 'rgb', 'rgba', 'bgr', 'bgra']
    responses:
      200:
        description: OK
      400:
        description: Bad Request
    """

    resolution = request.args.get("resolution")
    fileType = request.args.get("fileType")
    useVideoPort = request.args.get("useVideoPort")
    led = request.args.get("led")
    contrast = request.args.get("contrast")

    try:
        my_file = open("pi_" + str(datetime.now()) + "." + fileType, "wb")

        camera = PiCamera()
        camera.resolution = resolution
        camera.led = led
        camera.contrast = contrast

        camera.capture(output=my_file, format=fileType, use_video_port=useVideoPort)
        my_file.close()
        camera.close()
        return Response(response="OK, " + my_file.name, status=200, mimetype="text/plain")
    except Exception as err:
        my_file.close()
        camera.close()
        return Response(response=str(err), status=400, mimetype="text/plain")


# https://picamera.readthedocs.io/en/release-1.13/fov.html?highlight=resolution#sensor-modes
@app.route("/record/video", methods=["POST"])
def post_record_video():
    """Capture a video
    This is using docstrings for specifications.
    ---
    parameters:
      - name: resolution
        in: query
        required: false
        default: 1920x1080
        schema:
          type: string
        enum: ['2592x1944', '1920x1080', '1296x972', '1296x730', '640x480' ]
        description:
          2592x1944 max 15 fps, 1920x1080 max 30 fps, 1296x972 max 42 fps, 1296x730 max 49 fps, 640x480 max 90 fps
      - name: framerate
        in: query
        required: false
        default: 30
        schema:
          type: integer
      - name: contrast
        in: query
        required: false
        schema:
          type: integer
        description:
          Value between -100 and 100.
      - name: led
        in: query
        required: false
        default: true
        schema:
          type: boolean
      - name: fileType
        in: query
        required: false
        default: 'h264'
        schema:
          type: string
        enum: ['h264', 'mjpeg', 'yuv', 'rgb', 'rgba', 'bgr', 'bgra']
      - name: duration
        in: query
        required: false
        schema:
          type: integer
        description:
          Time in seconds for how long to record. 0 means record indefinitely (use stop request).
    responses:
      200:
        description: OK
      400:
        description: Bad Request
    """

    resolution = request.args.get("resolution")
    framerate = request.args.get("framerate")
    fileType = request.args.get("fileType")
    led = request.args.get("led")
    contrast = request.args.get("contrast")
    duration = request.args.get("duration")

    try:
        # Explicitly open a new file called my_image.jpg
        my_file = open("pi_" + str(datetime.now()) + "." + fileType, "wb")

        camera = PiCamera()
        camera.resolution = resolution
        camera.framerate = framerate
        camera.led = led
        camera.contrast = contrast
        camera.duration = duration

        camera.start_recording(output=my_file, format=fileType)
        if duration != 0:
            camera.wait_recording(duration)
            camera.stop_recording()
            my_file.close()
            camera.close()

        return Response(response="OK", status=200, mimetype="text/plain")
    except:
        camera.stop_recording()
        my_file.close()
        camera.close()
        return Response(response="NOK", status=400, mimetype="text/plain")


@app.route("/status/record/video", methods=["GET"])
def get_record_video_state():
    """Get video recording state info
    This is using docstrings for specifications.
    ---
    responses:
      200:
        description: OK
      400:
        description: Bad Request
    """

    try:
        camera = PiCamera()
        state = camera.recording
        if state == True:
            return Response(response="Recording", status=200, mimetype="text/plain")
        else:
            camera.close()
            return Response(response="Not Recording", status=200, mimetype="text/plain")
    except:
        return Response(response="An error occured.", status=400, mimetype="text/plain")


app.run(host="0.0.0.0", debug=True, port=6060)
