import cv2
import numpy as np
from scipy.spatial.transform import Rotation

def calculate_sharpness(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    return cv2.Laplacian(gray, cv2.CV_64F).var()

def detect_motion_blur(current_gray, prev_gray):
    if prev_gray is None:
        return 0
    try:
        flow = cv2.calcOpticalFlowFarneback(prev_gray, current_gray, None,
                                            0.5, 3, 15, 3, 5, 1.2, 0)
        magnitude = np.sqrt(flow[..., 0] ** 2 + flow[..., 1] ** 2)
        return np.mean(magnitude)
    except:
        return 0

def enhance_face_brightness(face_roi, gamma=1.5, clahe_enabled=True):
    lab = cv2.cvtColor(face_roi, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    if clahe_enabled:
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        l = clahe.apply(l)
    l_gamma = np.power(l / 255.0, 1.0 / gamma) * 255
    l_gamma = np.clip(l_gamma, 0, 255).astype(np.uint8)
    enhanced_lab = cv2.merge((l_gamma, a, b))
    return cv2.cvtColor(enhanced_lab, cv2.COLOR_LAB2BGR)

def darken_background(frame, factor):
    blurred = cv2.GaussianBlur(frame, (0, 0), 3)
    frame = cv2.addWeighted(frame, 0.7, blurred, 0.3, 0)
    return np.clip(frame.astype(np.float32) * factor, 0, 255).astype(np.uint8)

def estimate_pose(landmarks, frame_shape):
    try:
        image_points = np.array([
            landmarks[4], landmarks[152], landmarks[133],
            landmarks[362], landmarks[61], landmarks[291]
        ], dtype="double")

        model_points = np.array([
            (0.0, 0.0, 0.0), (0.0, -330.0, -65.0),
            (-165.0, 170.0, -135.0), (165.0, 170.0, -135.0),
            (-150.0, -150.0, -125.0), (150.0, -150.0, -125.0)
        ])

        focal_length = frame_shape[1]
        center = (frame_shape[1] / 2, frame_shape[0] / 2)
        camera_matrix = np.array([
            [focal_length, 0, center[0]],
            [0, focal_length, center[1]],
            [0, 0, 1]
        ], dtype="double")

        _, rotation_vector, _ = cv2.solvePnP(model_points, image_points, camera_matrix, None)
        r = Rotation.from_rotvec(rotation_vector.reshape(3))
        return r.as_euler('yxz', degrees=True)
    except:
        return 0, 0, 0
