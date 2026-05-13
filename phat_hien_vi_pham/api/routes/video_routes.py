from flask import Blueprint, jsonify, Response
import os
import cv2

video_bp = Blueprint(
    "video",
    __name__
)

VIDEO_FOLDER = "traffic_web/videos"

@video_bp.route("/videos")
def videos():

    data = []

    for file in os.listdir(VIDEO_FOLDER):

        if file.endswith(".mp4"):
            data.append(file)

    return jsonify(data)