#!/usr/bin/env python3

import argparse
import os
import queue
import signal
import threading

import cv2
import numpy as np
import rclpy
from cv_bridge import CvBridge
from rclpy.node import Node
from sensor_msgs.msg import Image
from ultralytics import YOLO


def default_camera_topic() -> str:
    machine_type = os.environ.get('MACHINE_TYPE', '')
    if machine_type == 'JetAuto':
        return '/depth_cam/rgb/image_raw'
    return '/usb_cam/image_raw'


def default_model_path() -> str:
    return '/home/ubuntu/third_party/yolo/yolov11/yolo11s.pt'


def clamp(value: int, lower: int, upper: int) -> int:
    return max(lower, min(upper, value))


class ObjectDetector(Node):
    def __init__(self, topic: str, model_path: str, confidence: float, window_name: str, mode: str, color_threshold: float):
        super().__init__('jetauto_object_detector')
        self.bridge = CvBridge()
        self.window_name = window_name
        self.confidence = confidence
        self.mode = mode
        self.color_threshold = color_threshold
        self.model = YOLO(model_path) if mode == 'detect' else None
        self.frames = queue.Queue(maxsize=2)
        self.running = True
        self.selected_point = None
        self.target_lab = None
        self.target_bgr = None
        self.mouse_lock = threading.Lock()

        self.subscription = self.create_subscription(Image, topic, self.image_callback, 10)
        self.get_logger().info(f'Subscribed to {topic}')
        self.get_logger().info(f'Mode: {mode}')
        if self.model is not None:
            self.get_logger().info(f'Using model {model_path}')

        signal.signal(signal.SIGINT, self.handle_signal)
        threading.Thread(target=self.process_frames, daemon=True).start()

    def handle_signal(self, signum, frame):
        self.running = False

    def image_callback(self, msg: Image) -> None:
        try:
            frame = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
        except Exception:
            frame = self.bridge.imgmsg_to_cv2(msg)

        if self.frames.full():
            try:
                self.frames.get_nowait()
            except queue.Empty:
                pass
        self.frames.put(frame)

    def mouse_callback(self, event, x, y, flags, param) -> None:
        if event != cv2.EVENT_LBUTTONDOWN or param is None:
            return

        frame = param
        h, w = frame.shape[:2]
        x = clamp(x, 0, w - 1)
        y = clamp(y, 0, h - 1)

        patch_radius = 2
        x1 = clamp(x - patch_radius, 0, w - 1)
        x2 = clamp(x + patch_radius, 0, w - 1)
        y1 = clamp(y - patch_radius, 0, h - 1)
        y2 = clamp(y + patch_radius, 0, h - 1)

        patch = frame[y1:y2 + 1, x1:x2 + 1]
        if patch.size == 0:
            return

        patch_lab = cv2.cvtColor(patch, cv2.COLOR_BGR2LAB)
        mean_lab = patch_lab.reshape(-1, 3).mean(axis=0)
        mean_bgr = patch.reshape(-1, 3).mean(axis=0)

        with self.mouse_lock:
            self.selected_point = (x, y)
            self.target_lab = mean_lab
            self.target_bgr = tuple(int(v) for v in mean_bgr)
            self.get_logger().info(
                f'Selected color at ({x}, {y}) -> BGR {self.target_bgr[0]}, {self.target_bgr[1]}, {self.target_bgr[2]}'
            )

    def process_frames(self) -> None:
        while self.running:
            try:
                frame = self.frames.get(timeout=1.0)
            except queue.Empty:
                continue

            try:
                if self.mode == 'detect':
                    result = self.model(frame, conf=self.confidence, imgsz=640, verbose=False)[0]
                    annotated = result.plot()

                    if result.boxes is not None and len(result.boxes) > 0:
                        detections = []
                        for box in result.boxes:
                            cls_id = int(box.cls[0])
                            score = float(box.conf[0])
                            x1, y1, x2, y2 = map(int, box.xyxy[0])
                            class_name = self.model.names.get(cls_id, str(cls_id))
                            detections.append(f'{class_name}:{score:.2f} [{x1},{y1},{x2},{y2}]')
                        self.get_logger().info(' | '.join(detections))

                    display_frame = annotated
                else:
                    display_frame = self.track_selected_color(frame)

                cv2.setMouseCallback(self.window_name, self.mouse_callback, display_frame)
                cv2.imshow(self.window_name, display_frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    self.running = False
                    break
            except Exception as exc:
                self.get_logger().error(f'Detection error: {exc}')

        cv2.destroyAllWindows()
        rclpy.shutdown()

    def track_selected_color(self, frame):
        annotated = frame.copy()
        with self.mouse_lock:
            selected_point = self.selected_point
            target_lab = None if self.target_lab is None else np.array(self.target_lab, dtype=np.float32)
            target_bgr = self.target_bgr

        if target_lab is None:
            cv2.putText(
                annotated,
                'Click a red, green, or blue square to start tracking',
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 255),
                2,
            )
            return annotated

        frame_lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
        frame_lab = cv2.GaussianBlur(frame_lab, (5, 5), 0)

        lower = np.array([
            clamp(int(target_lab[0] - 50 * self.color_threshold * 2), 0, 255),
            clamp(int(target_lab[1] - 50 * self.color_threshold), 0, 255),
            clamp(int(target_lab[2] - 50 * self.color_threshold), 0, 255),
        ], dtype=np.uint8)
        upper = np.array([
            clamp(int(target_lab[0] + 50 * self.color_threshold * 2), 0, 255),
            clamp(int(target_lab[1] + 50 * self.color_threshold), 0, 255),
            clamp(int(target_lab[2] + 50 * self.color_threshold), 0, 255),
        ], dtype=np.uint8)

        mask = cv2.inRange(frame_lab, lower, upper)
        mask = cv2.erode(mask, cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3)))
        mask = cv2.dilate(mask, cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3)))

        contours = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)[-2]
        contours = [contour for contour in contours if abs(cv2.contourArea(contour)) > 40]

        if contours:
            contour = max(contours, key=cv2.contourArea)
            (cx, cy), radius = cv2.minEnclosingCircle(contour)
            cx_i, cy_i, radius_i = int(cx), int(cy), max(1, int(radius))

            cv2.circle(annotated, (cx_i, cy_i), radius_i, target_bgr if target_bgr is not None else (0, 255, 0), 2)
            cv2.circle(annotated, (cx_i, cy_i), 4, (255, 255, 0), -1)
            cv2.putText(
                annotated,
                f'tracking: {target_bgr[2]},{target_bgr[1]},{target_bgr[0]}' if target_bgr is not None else 'tracking',
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 255),
                2,
            )
        else:
            cv2.putText(
                annotated,
                'target lost - click another square',
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 0, 255),
                2,
            )

        if selected_point is not None:
            cv2.circle(annotated, selected_point, 5, (255, 255, 0), -1)

        return annotated


def main() -> None:
    parser = argparse.ArgumentParser(description='Run object detection on the JetAuto camera stream.')
    parser.add_argument('--topic', default=default_camera_topic(), help='ROS image topic to subscribe to')
    parser.add_argument('--model', default=default_model_path(), help='Path to a YOLO weights file')
    parser.add_argument('--confidence', type=float, default=0.35, help='Detection confidence threshold')
    parser.add_argument('--mode', choices=['detect', 'color'], default='color', help='detect for YOLO boxes or color for click-to-track')
    parser.add_argument('--color-threshold', type=float, default=0.10, help='LAB threshold scale used for color tracking')
    parser.add_argument('--window-name', default='JetAuto Object Detection', help='OpenCV window name')
    args = parser.parse_args()

    if args.mode == 'detect' and not os.path.exists(args.model):
        raise FileNotFoundError(f'Model not found: {args.model}')

    rclpy.init()
    node = ObjectDetector(args.topic, args.model, args.confidence, args.window_name, args.mode, args.color_threshold)

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.running = False
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
        cv2.destroyAllWindows()


if __name__ == '__main__':
    main()