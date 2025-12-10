from flask import Blueprint, Response, jsonify
import cv2
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from __main__ import FaceDetector

detection_bp = Blueprint('detection', __name__)

# Global detector instance
detector = None
camera = None


def get_detector():
    """Get or create face detector instance"""
    global detector
    if detector is None:
        detector = FaceDetector()
    return detector


def get_camera():
    """Get or create camera instance"""
    global camera
    if camera is None or not camera.isOpened():
        camera = cv2.VideoCapture(0)
    return camera


def generate_frames():
    """Generate video frames with face detection"""
    face_detector = get_detector()
    cap = get_camera()

    while True:
        success, frame = cap.read()
        if not success:
            break

        # Detect movement
        direction, annotated_frame = face_detector.detect_movement(frame)

        # Encode frame to JPEG
        ret, buffer = cv2.imencode('.jpg', annotated_frame)
        frame_bytes = buffer.tobytes()

        # Yield frame in multipart format
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')


@detection_bp.route('/video_feed')
def video_feed():
    """Video streaming route"""
    return Response(
        generate_frames(),
        mimetype='multipart/x-mixed-replace; boundary=frame'
    )


@detection_bp.route('/start')
def start_detection():
    """Start detection session"""
    try:
        face_detector = get_detector()
        cap = get_camera()

        if cap.isOpened():
            return jsonify({
                "status": "success",
                "message": "Detection started"
            }), 200
        else:
            return jsonify({
                "status": "error",
                "message": "Could not access camera"
            }), 500
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


@detection_bp.route('/stop')
def stop_detection():
    """Stop detection and release camera"""
    global camera, detector

    try:
        if camera is not None:
            camera.release()
            camera = None

        if detector is not None:
            detector.release()
            detector = None

        return jsonify({
            "status": "success",
            "message": "Detection stopped"
        }), 200
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


@detection_bp.route('/recalibrate')
def recalibrate():
    """Recalibrate face detection"""
    try:
        face_detector = get_detector()
        face_detector.recalibrate()

        return jsonify({
            "status": "success",
            "message": "Recalibrated successfully"
        }), 200
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


@detection_bp.route('/status')
def detection_status():
    """Check detection status"""
    global camera

    is_active = camera is not None and camera.isOpened()

    return jsonify({
        "active": is_active,
        "message": "Detection is active" if is_active else "Detection is inactive"
    }), 200