#!/usr/bin/env python3

import argparse
import os

import cv2
import rclpy
from cv_bridge import CvBridge
from rclpy.node import Node
from sensor_msgs.msg import Image


def default_camera_topic() -> str:
    machine_type = os.environ.get('MACHINE_TYPE', '')
    if machine_type == 'JetAuto':
        return '/depth_cam/rgb/image_raw'
    return '/usb_cam/image_raw'


class CameraViewer(Node):
    def __init__(self, topic: str, window_name: str):
        super().__init__('jetauto_camera_viewer')
        self.bridge = CvBridge()
        self.window_name = window_name
        self.subscription = self.create_subscription(Image, topic, self.image_callback, 10)
        self.get_logger().info(f'Subscribed to {topic}')

    def image_callback(self, msg: Image) -> None:
        try:
            frame = self.bridge.imgmsg_to_cv2(msg, desired_encoding='rgb8')
        except Exception:
            frame = self.bridge.imgmsg_to_cv2(msg)

        bgr_frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        cv2.imshow(self.window_name, bgr_frame)
        cv2.waitKey(1)


def main() -> None:
    parser = argparse.ArgumentParser(description='Display the JetAuto camera stream.')
    parser.add_argument('--topic', default=default_camera_topic(), help='ROS image topic to display')
    parser.add_argument('--window-name', default='JetAuto Camera', help='OpenCV window name')
    args = parser.parse_args()

    rclpy.init()
    node = CameraViewer(args.topic, args.window_name)

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()
        cv2.destroyAllWindows()


if __name__ == '__main__':
    main()