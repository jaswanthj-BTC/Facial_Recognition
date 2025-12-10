import cv2
import mediapipe as mp
import numpy as np


class FaceDetector:
    def __init__(self):
        # Initialize MediaPipe Face Mesh
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        self.mp_drawing = mp.solutions.drawing_utils
        self.drawing_spec = self.mp_drawing.DrawingSpec(thickness=1, circle_radius=1)

        # Reference points for head position
        self.reference_nose_tip = None
        self.calibrated = False

    def detect_movement(self, frame):
        """
        Detect facial landmarks and determine head movement direction
        Returns: direction (LEFT, RIGHT, UP, DOWN, CENTER) and annotated frame
        """

        # Convert BGR to RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Process the frame
        results = self.face_mesh.process(rgb_frame)

        direction = "NO FACE"

        if results.multi_face_landmarks:
            face_landmarks = results.multi_face_landmarks[0]

            # Get image dimensions
            h, w, c = frame.shape

            # Key landmark indices
            # Nose tip: 1
            # Left eye: 33
            # Right eye: 263
            # Chin: 152
            # Forehead: 10

            nose_tip = face_landmarks.landmark[1]
            nose_x = int(nose_tip.x * w)
            nose_y = int(nose_tip.y * h)

            # Draw landmarks on face
            self.mp_drawing.draw_landmarks(
                image=frame,
                landmark_list=face_landmarks,
                connections=self.mp_face_mesh.FACEMESH_TESSELATION,
                landmark_drawing_spec=None,
                connection_drawing_spec=self.mp_drawing.DrawingSpec(
                    color=(0, 255, 0), thickness=1, circle_radius=1
                )
            )

            # Calibrate on first detection or recalibrate
            if not self.calibrated or self.reference_nose_tip is None:
                self.reference_nose_tip = (nose_x, nose_y)
                self.calibrated = True
                direction = "CENTER (Calibrated)"
            else:
                # Calculate displacement from reference
                dx = nose_x - self.reference_nose_tip[0]
                dy = nose_y - self.reference_nose_tip[1]

                # Thresholds for movement detection
                horizontal_threshold = w * 0.05  # 5% of width
                vertical_threshold = h * 0.05  # 5% of height

                # Determine direction
                if abs(dx) > horizontal_threshold or abs(dy) > vertical_threshold:
                    if abs(dx) > abs(dy):
                        # Horizontal movement is dominant
                        if dx > horizontal_threshold:
                            direction = "RIGHT"
                        elif dx < -horizontal_threshold:
                            direction = "LEFT"
                    else:
                        # Vertical movement is dominant
                        if dy > vertical_threshold:
                            direction = "DOWN"
                        elif dy < -vertical_threshold:
                            direction = "UP"
                else:
                    direction = "CENTER"

                # Draw reference point
                cv2.circle(frame, self.reference_nose_tip, 5, (255, 0, 0), -1)

                # Draw current nose position
                cv2.circle(frame, (nose_x, nose_y), 5, (0, 0, 255), -1)

                # Draw line between reference and current
                cv2.line(frame, self.reference_nose_tip, (nose_x, nose_y), (255, 255, 0), 2)

            # Display direction on frame
            cv2.putText(frame, f"Direction: {direction}", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

            # Display instructions
            cv2.putText(frame, "Press 'C' to recalibrate", (10, h - 20),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

        else:
            cv2.putText(frame, "No face detected", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

        return direction, frame

    def recalibrate(self):
        """Reset calibration"""
        self.reference_nose_tip = None
        self.calibrated = False

    def release(self):
        """Release resources"""
        self.face_mesh.close()


# Standalone test function
def test_camera():
    """Test the face detection with webcam"""
    detector = FaceDetector()
    cap = cv2.VideoCapture(0)

    print("Press 'C' to recalibrate")
    print("Press 'Q' to quit")

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        # Detect movement
        direction, annotated_frame = detector.detect_movement(frame)

        # Display
        cv2.imshow('Facial Movement Detection', annotated_frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('c'):
            detector.recalibrate()
            print("Recalibrated!")

    cap.release()
    cv2.destroyAllWindows()
    detector.release()


if __name__ == "__main__":
    test_camera()
