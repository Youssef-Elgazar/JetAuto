#!/usr/bin/env python3
"""
JetAuto person-follower.

Extends the existing object-detection pattern (same camera subscription,
same YOLO model, same threaded frame-processing queue) but:
  - filters detections down to the "person" class only
  - picks the largest detected person as the follow target
  - drives a proportional controller that publishes geometry_msgs/Twist
    to /controller/cmd_vel to keep that person centered and at a target
    following distance (approximated by bounding-box height)

Run it the same way you'd run the detector-only script:
    python3 jetauto_person_follower.py
Press 'q' in the preview window, or Ctrl+C in the terminal, to stop.
Movement is only ever commanded while a person is detected; loss of
detection for more than --lost-frames consecutive frames sends a zero
Twist and holds the robot still until a person is found again.

NOTE ON DIRECTION: the follow math computes a positive linear_x when the
target is farther than desired (i.e. "drive forward"), assuming positive
Twist.linear.x == forward per REP-103. Some JetAuto/Hiwonder base
configurations wire the drive controller so that positive linear.x is
actually reverse. If the robot backs away from the person instead of
approaching, run with --invert-linear (see main() for a quick manual
test you can run first to confirm which way is "true" forward).
"""

import argparse
import os
import queue
import signal
import threading

import cv2
import rclpy
from cv_bridge import CvBridge
from geometry_msgs.msg import Twist
from rclpy.node import Node
from ultralytics import YOLO
from sensor_msgs.msg import Image

PERSON_CLASS_NAME = 'person'


def default_camera_topic() -> str:
    machine_type = os.environ.get('MACHINE_TYPE', '')
    if machine_type == 'JetAuto':
        return '/depth_cam/rgb/image_raw'
    return '/usb_cam/image_raw'


def default_model_path() -> str:
    return '/home/ubuntu/third_party/yolo/yolov11/yolo11s.pt'


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


class PersonFollower(Node):
    def __init__(
        self,
        topic: str,
        model_path: str,
        confidence: float,
        window_name: str,
        cmd_vel_topic: str,
        target_box_ratio: float,
        max_linear_speed: float,
        max_angular_speed: float,
        linear_gain: float,
        angular_gain: float,
        distance_deadband: float,
        center_deadband: float,
        lost_frames: int,
        show_window: bool,
        invert_linear: bool = False,
    ):
        super().__init__('jetauto_person_follower')
        self.bridge = CvBridge()
        self.window_name = window_name
        self.confidence = confidence
        self.model = YOLO(model_path)
        self.frames = queue.Queue(maxsize=2)
        self.running = True
        self.show_window = show_window

        self.target_box_ratio = target_box_ratio
        self.max_linear_speed = max_linear_speed
        self.max_angular_speed = max_angular_speed
        self.linear_gain = linear_gain
        self.angular_gain = angular_gain
        self.distance_deadband = distance_deadband
        self.center_deadband = center_deadband
        self.lost_frames_threshold = lost_frames
        self.frames_since_seen = lost_frames  # start "lost" so we don't move at boot
        self.invert_linear = invert_linear

        person_ids = [cls_id for cls_id, name in self.model.names.items() if name == PERSON_CLASS_NAME]
        if not person_ids:
            raise RuntimeError(f"Model at {model_path} has no '{PERSON_CLASS_NAME}' class in its label set")
        self.person_class_id = person_ids[0]

        self.cmd_pub = self.create_publisher(Twist, cmd_vel_topic, 10)
        self.subscription = self.create_subscription(Image, topic, self.image_callback, 10)
        self.get_logger().info(f'Subscribed to {topic}')
        self.get_logger().info(f'Publishing Twist to {cmd_vel_topic}')
        self.get_logger().info(f'Using model {model_path} (person class id {self.person_class_id})')
        if self.invert_linear:
            self.get_logger().info('Linear direction inverted (--invert-linear set)')

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

    def publish_twist(self, linear_x: float, angular_z: float) -> None:
        twist = Twist()
        twist.linear.x = clamp(linear_x, -self.max_linear_speed, self.max_linear_speed)
        twist.angular.z = clamp(angular_z, -self.max_angular_speed, self.max_angular_speed)
        self.cmd_pub.publish(twist)

    def stop(self) -> None:
        self.publish_twist(0.0, 0.0)

    def best_person_box(self, result):
        """Return (x1, y1, x2, y2) for the largest person detection, or None."""
        if result.boxes is None or len(result.boxes) == 0:
            return None

        best_box = None
        best_area = 0.0
        for box in result.boxes:
            cls_id = int(box.cls[0])
            if cls_id != self.person_class_id:
                continue
            x1, y1, x2, y2 = map(float, box.xyxy[0])
            area = max(0.0, x2 - x1) * max(0.0, y2 - y1)
            if area > best_area:
                best_area = area
                best_box = (x1, y1, x2, y2)
        return best_box

    def compute_control(self, box, frame_width: int, frame_height: int):
        x1, y1, x2, y2 = box
        box_center_x = (x1 + x2) / 2.0
        box_height = max(1.0, y2 - y1)

        frame_center_x = frame_width / 2.0
        # Normalized horizontal offset in [-1, 1]; positive = person is to the right.
        offset_x = (box_center_x - frame_center_x) / frame_center_x

        # Normalized box height in [0, 1]; larger = person appears closer.
        height_ratio = box_height / frame_height

        # Positive distance_error means the person is farther than target (box too small) -> move forward.
        distance_error = self.target_box_ratio - height_ratio

        angular_z = -self.angular_gain * offset_x
        if abs(offset_x) < self.center_deadband:
            angular_z = 0.0

        linear_x = self.linear_gain * distance_error
        if abs(distance_error) < self.distance_deadband:
            linear_x = 0.0

        # See NOTE ON DIRECTION at top of file: flips forward/back if this
        # base's controller treats positive linear.x as reverse.
        if self.invert_linear:
            linear_x = -linear_x

        return linear_x, angular_z, offset_x, height_ratio

    def process_frames(self) -> None:
        while self.running:
            try:
                frame = self.frames.get(timeout=1.0)
            except queue.Empty:
                continue

            try:
                result = self.model(frame, conf=self.confidence, imgsz=640, verbose=False)[0]
                annotated = result.plot()
                frame_height, frame_width = frame.shape[:2]

                box = self.best_person_box(result)

                if box is not None:
                    self.frames_since_seen = 0
                    linear_x, angular_z, offset_x, height_ratio = self.compute_control(
                        box, frame_width, frame_height
                    )
                    self.publish_twist(linear_x, angular_z)
                    self.get_logger().info(
                        f'person offset_x={offset_x:.2f} height_ratio={height_ratio:.2f} '
                        f'-> linear_x={linear_x:.2f} angular_z={angular_z:.2f}'
                    )
                    x1, y1, x2, y2 = map(int, box)
                    cv2.rectangle(annotated, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    cv2.circle(annotated, (int((x1 + x2) / 2), int((y1 + y2) / 2)), 5, (0, 255, 0), -1)
                else:
                    self.frames_since_seen += 1
                    if self.frames_since_seen >= self.lost_frames_threshold:
                        self.stop()
                        if self.frames_since_seen == self.lost_frames_threshold:
                            self.get_logger().info('Person lost — holding position')

                if self.show_window:
                    cv2.imshow(self.window_name, annotated)
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        self.running = False
                        break
            except Exception as exc:
                self.get_logger().error(f'Detection error: {exc}')
                self.stop()

        self.stop()
        cv2.destroyAllWindows()
        rclpy.shutdown()


def main() -> None:
    parser = argparse.ArgumentParser(description='Follow the largest detected person using the JetAuto camera stream.')
    parser.add_argument('--topic', default=default_camera_topic(), help='ROS image topic to subscribe to')
    parser.add_argument('--model', default=default_model_path(), help='Path to a YOLO weights file')
    parser.add_argument('--confidence', type=float, default=0.5, help='Detection confidence threshold')
    parser.add_argument('--window-name', default='JetAuto Person Follower', help='OpenCV window name')
    parser.add_argument('--cmd-vel-topic', default='/controller/cmd_vel', help='Twist topic to publish to')
    parser.add_argument('--target-box-ratio', type=float, default=0.45,
                         help='Desired person bounding-box height as a fraction of frame height (bigger = follow closer)')
    parser.add_argument('--max-linear-speed', type=float, default=0.15, help='Max forward/backward speed (m/s)')
    parser.add_argument('--max-angular-speed', type=float, default=0.8, help='Max turn speed (rad/s)')
    parser.add_argument('--linear-gain', type=float, default=0.6, help='Proportional gain for forward/backward speed')
    parser.add_argument('--angular-gain', type=float, default=1.0, help='Proportional gain for turn speed')
    parser.add_argument('--distance-deadband', type=float, default=0.03,
                         help='Ignore distance error smaller than this (fraction of frame height)')
    parser.add_argument('--center-deadband', type=float, default=0.05,
                         help='Ignore horizontal offset smaller than this (fraction of half frame width)')
    parser.add_argument('--lost-frames', type=int, default=5,
                         help='Consecutive frames with no person detected before stopping')
    parser.add_argument('--no-window', action='store_true', help='Disable the OpenCV preview window')
    parser.add_argument('--invert-linear', action='store_true',
                         help='Flip forward/backward direction. Use this if the robot backs away from '
                              'a person instead of approaching (some JetAuto bases treat positive '
                              'linear.x as reverse). Test with the manual check in the module docstring '
                              'before enabling if unsure.')
    args = parser.parse_args()

    if not os.path.exists(args.model):
        raise FileNotFoundError(f'Model not found: {args.model}')

    rclpy.init()
    node = PersonFollower(
        topic=args.topic,
        model_path=args.model,
        confidence=args.confidence,
        window_name=args.window_name,
        cmd_vel_topic=args.cmd_vel_topic,
        target_box_ratio=args.target_box_ratio,
        max_linear_speed=args.max_linear_speed,
        max_angular_speed=args.max_angular_speed,
        linear_gain=args.linear_gain,
        angular_gain=args.angular_gain,
        distance_deadband=args.distance_deadband,
        center_deadband=args.center_deadband,
        lost_frames=args.lost_frames,
        show_window=not args.no_window,
        invert_linear=args.invert_linear,
    )

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.running = False
        node.stop()
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
        cv2.destroyAllWindows()


if __name__ == '__main__':
    main()