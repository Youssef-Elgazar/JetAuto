#!/usr/bin/env python3

import argparse
import os
import queue
import signal
import threading

import cv2
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


class ObjectDetector(Node):
    def __init__(self, topic: str, model_path: str, confidence: float, window_name: str):
        super().__init__('jetauto_object_detector_only')
        self.bridge = CvBridge()
        self.window_name = window_name
        self.confidence = confidence
        self.model = YOLO(model_path)
        self.frames = queue.Queue(maxsize=2)
        self.running = True

        self.subscription = self.create_subscription(Image, topic, self.image_callback, 10)
        self.get_logger().info(f'Subscribed to {topic}')
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

    def process_frames(self) -> None:
        while self.running:
            try:
                frame = self.frames.get(timeout=1.0)
            except queue.Empty:
                continue

            try:
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

                cv2.imshow(self.window_name, annotated)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    self.running = False
                    break
            except Exception as exc:
                self.get_logger().error(f'Detection error: {exc}')

        cv2.destroyAllWindows()
        rclpy.shutdown()


def main() -> None:
    parser = argparse.ArgumentParser(description='Run pure object detection on the JetAuto camera stream.')
    parser.add_argument('--topic', default=default_camera_topic(), help='ROS image topic to subscribe to')
    parser.add_argument('--model', default=default_model_path(), help='Path to a YOLO weights file')
    parser.add_argument('--confidence', type=float, default=0.35, help='Detection confidence threshold')
    parser.add_argument('--window-name', default='JetAuto Object Detection', help='OpenCV window name')
    args = parser.parse_args()

    if not os.path.exists(args.model):
        raise FileNotFoundError(f'Model not found: {args.model}')

    rclpy.init()
    node = ObjectDetector(args.topic, args.model, args.confidence, args.window_name)

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