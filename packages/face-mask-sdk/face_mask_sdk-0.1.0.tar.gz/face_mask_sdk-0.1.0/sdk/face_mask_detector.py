import cv2
import numpy as np
from ultralytics import YOLO
from mediapipe.python.solutions import face_detection, face_mesh
from scipy.spatial.transform import Rotation
from collections import deque
import warnings
from typing import Optional, List, Dict, Any, Tuple

class FaceMaskDetector:
    """口罩检测SDK主类"""
    
    def __init__(self, model_path: str = "./best.pt", camera_id: int = 0):
        """
        初始化口罩检测器
        
        Args:
            model_path (str): YOLO模型路径
            camera_id (int): 摄像头ID
        """
        # 忽略MediaPipe的特定警告
        warnings.filterwarnings("ignore", category=UserWarning)
        
        # 创建人脸检测器实例
        self.face_detection = face_detection.FaceDetection(
            min_detection_confidence=0.7,
            model_selection=1
        )
        
        # 创建面部网格检测器实例
        self.face_mesh = face_mesh.FaceMesh(
            static_image_mode=False,
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.7
        )
        
        # 加载YOLO口罩检测模型
        self.mask_model = YOLO(model_path)
        
        # 初始化摄像头
        self.cap = cv2.VideoCapture(camera_id)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        self.cap.set(cv2.CAP_PROP_FPS, 30)
        
        # 初始化参数
        self.brightness_factor = 1.5
        self.darken_factor = 0.7
        self.stable_frames_threshold = 3
        self.sharpness_threshold = 50
        self.motion_blur_threshold = 100
        
        # 初始化人脸历史记录队列
        self.face_history = deque(maxlen=5)
        self.prev_gray: Optional[np.ndarray] = None
        
        # 定义颜色常量
        self.COLORS = {
            'no_mask': (0, 255, 0),
            'mask': (0, 0, 255),
            'warning': (0, 255, 255),
            'info': (255, 255, 255),
            'stable': (255, 0, 0)
        }

    def calculate_sharpness(self, image):
        """计算图像清晰度"""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        return cv2.Laplacian(gray, cv2.CV_64F).var()

    def detect_motion_blur(self, current_gray, prev_gray):
        """检测运动模糊"""
        if prev_gray is None:
            return 0
        try:
            flow = cv2.calcOpticalFlowFarneback(
                prev_gray, current_gray,
                np.zeros((prev_gray.shape[0], prev_gray.shape[1], 2), dtype=np.float32),
                0.5, 3, 15, 3, 5, 1.2, 0
            )
            magnitude = np.sqrt(flow[..., 0] ** 2 + flow[..., 1] ** 2)
            return np.mean(magnitude)
        except:
            return 0

    def enhance_face_brightness(self, face_roi, gamma=1.5, clahe_enabled=True):
        """增强人脸亮度"""
        lab = cv2.cvtColor(face_roi, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        
        if clahe_enabled:
            clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
            l = clahe.apply(l)
        
        l_gamma = np.power(l / 255.0, 1.0 / gamma) * 255
        l_gamma = np.clip(l_gamma, 0, 255).astype(np.uint8)
        
        enhanced_lab = cv2.merge((l_gamma, a, b))
        return cv2.cvtColor(enhanced_lab, cv2.COLOR_LAB2BGR)

    def darken_background(self, frame, factor=None):
        """使背景变暗"""
        if factor is None:
            factor = self.darken_factor
        blurred = cv2.GaussianBlur(frame, (0, 0), 3)
        frame = cv2.addWeighted(frame, 0.7, blurred, 0.3, 0)
        return np.clip(frame.astype(np.float32) * factor, 0, 255).astype(np.uint8)

    def estimate_pose(self, landmarks, frame_shape):
        """估计头部姿态"""
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
            
            dist_coeffs = np.zeros((4, 1))
            _, rotation_vector, _ = cv2.solvePnP(
                model_points, image_points,
                camera_matrix, dist_coeffs,
                flags=cv2.SOLVEPNP_ITERATIVE
            )
            
            r = Rotation.from_rotvec(rotation_vector.reshape(3))
            yaw, pitch, roll = r.as_euler('yxz', degrees=True)
            return yaw, pitch, roll
        except:
            return 0, 0, 0

    def analyze_face(self, frame, face_roi):
        """分析人脸特征"""
        results = {}
        results['sharpness'] = self.calculate_sharpness(face_roi)
        gray = cv2.cvtColor(face_roi, cv2.COLOR_BGR2GRAY)
        results['brightness'] = np.mean(gray)
        
        try:
            mask_results = self.mask_model.predict(face_roi, imgsz=160, conf=0.6, verbose=False)
            results['mask'] = any(box.cls == 0 for box in mask_results[0].boxes) if mask_results[0].boxes else False
        except:
            results['mask'] = False
        
        return results

    def is_face_stable(self, current_bbox, history):
        """判断人脸是否稳定"""
        if len(history) < self.stable_frames_threshold:
            return False
        
        movements = []
        for prev_bbox in history:
            dx = abs(current_bbox[0] - prev_bbox[0]) / current_bbox[2]
            dy = abs(current_bbox[1] - prev_bbox[1]) / current_bbox[3]
            movements.append(dx + dy)
        
        return np.mean(movements) < 0.1

    def process_frame(self, frame: Optional[np.ndarray] = None) -> Optional[Dict[str, Any]]:
        """
        处理单帧图像
        
        Args:
            frame: 输入帧，如果为None则从摄像头读取
            
        Returns:
            dict: 包含处理结果的字典，如果处理失败则返回None
        """
        if frame is None:
            success, frame = self.cap.read()
            if not success:
                return None
        
        # 运动模糊检测
        current_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        motion_blur = self.detect_motion_blur(current_gray, self.prev_gray)
        self.prev_gray = current_gray
        
        # 预处理帧
        processed_frame = self.darken_background(frame)
        rgb_frame = cv2.cvtColor(processed_frame, cv2.COLOR_BGR2RGB)
        
        results = {
            'frame': processed_frame,
            'detections': [],
            'motion_blur': motion_blur
        }
        
        # 人脸检测
        face_results = self.face_detection.process(rgb_frame)
        if hasattr(face_results, 'detections') and face_results.detections:
            for detection in face_results.detections:
                bbox = detection.location_data.relative_bounding_box
                h, w = frame.shape[:2]
                x1 = int(bbox.xmin * w)
                y1 = int(bbox.ymin * h)
                x2 = int((bbox.xmin + bbox.width) * w)
                y2 = int((bbox.ymin + bbox.height) * h)
                x1, y1 = max(0, x1), max(0, y1)
                x2, y2 = min(w, x2), min(h, y2)
                
                if (x2 - x1) < 50 or (y2 - y1) < 50:
                    continue
                
                current_bbox = (x1, y1, x2, y2)
                self.face_history.append(current_bbox)
                stable = self.is_face_stable(current_bbox, self.face_history)
                
                face_roi = processed_frame[y1:y2, x1:x2]
                if face_roi.size != 0:
                    enhanced_face = self.enhance_face_brightness(face_roi)
                    processed_frame[y1:y2, x1:x2] = enhanced_face
                
                mesh_results = self.face_mesh.process(rgb_frame)
                if hasattr(mesh_results, 'multi_face_landmarks') and mesh_results.multi_face_landmarks:
                    landmarks = []
                    for landmark in mesh_results.multi_face_landmarks[0].landmark:
                        landmarks.append((int(landmark.x * w), int(landmark.y * h)))
                    
                    yaw, pitch, roll = self.estimate_pose(landmarks, frame.shape)
                    
                    if face_roi.size != 0 and motion_blur < self.motion_blur_threshold:
                        metrics = self.analyze_face(frame, face_roi)
                        detection_result = {
                            'bbox': (x1, y1, x2, y2),
                            'pose': (yaw, pitch, roll),
                            'metrics': metrics,
                            'stable': stable
                        }
                        results['detections'].append(detection_result)
        
        return results

    def release(self):
        """释放资源"""
        self.cap.release()
        cv2.destroyAllWindows()

    def set_brightness_factor(self, factor):
        """设置亮度增强因子"""
        self.brightness_factor = max(1.0, min(2.5, factor))

    def set_darken_factor(self, factor):
        """设置背景变暗因子"""
        self.darken_factor = max(0.3, min(1.0, factor)) 