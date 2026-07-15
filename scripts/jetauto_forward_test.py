#!/usr/bin/env python3

import time

import rclpy
from geometry_msgs.msg import Twist
from rclpy.node import Node


class ForwardTest(Node):
    def __init__(self):
        super().__init__('jetauto_forward_test')
        self.publisher = self.create_publisher(Twist, '/controller/cmd_vel', 1)

    def publish_forward(self, speed: float) -> None:
        twist = Twist()
        twist.linear.x = speed
        self.publisher.publish(twist)

    def stop(self) -> None:
        self.publisher.publish(Twist())


def main() -> None:
    rclpy.init()
    node = ForwardTest()

    try:
        print('Publishing forward motion for 2 seconds...')
        node.publish_forward(0.15)
        time.sleep(2.0)
    finally:
        node.stop()
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
        print('Stopped.')


if __name__ == '__main__':
    main()