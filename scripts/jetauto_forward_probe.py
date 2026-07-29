#!/usr/bin/env python3

import argparse
import time
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry

class JetAutoForwardProbe(Node):
    def __init__(self, speed: float, duration: float, publish_hz: float):
        super().__init__('jetauto_forward_probe')
        self.speed = speed
        self.duration = duration
        self.publish_hz = publish_hz
        self.odom_x = None
        self.odom_y = None

        self.publisher = self.create_publisher(Twist, '/controller/cmd_vel', 1)
        self.subscription = self.create_subscription(Odometry, '/odom_raw', self.odom_callback, 10)

    def odom_callback(self, msg: Odometry) -> None:
        self.odom_x = msg.pose.pose.position.x
        self.odom_y = msg.pose.pose.position.y

    def run(self) -> int:
        self.get_logger().info(f'Forward probe: speed={self.speed} duration={self.duration}s')
        twist = Twist()
        twist.linear.x = self.speed

        total_steps = int(self.duration * self.publish_hz)
        sleep_time = 1.0 / self.publish_hz
        self.get_logger().info('Waiting for odometry updates...')
        start_time = time.time()
        self.wait_for_odom(timeout=3.0)

        initial_x = self.odom_x if self.odom_x is not None else 0.0
        initial_y = self.odom_y if self.odom_y is not None else 0.0

        for step in range(total_steps):
            self.publisher.publish(twist)
            now = time.time()
            if self.odom_x is not None:
                dx = self.odom_x - initial_x
                dy = self.odom_y - initial_y
                self.get_logger().info(f'[{step+1}/{total_steps}] odom x={self.odom_x:.4f} dx={dx:.4f} y={self.odom_y:.4f} dy={dy:.4f}')
            else:
                self.get_logger().warn(f'[{step+1}/{total_steps}] no odom reading yet')
            time.sleep(sleep_time)

        self.publisher.publish(Twist())
        elapsed = time.time() - start_time
        self.get_logger().info(f'Probe complete, elapsed={elapsed:.2f}s')
        if self.odom_x is not None:
            self.get_logger().info(f'Final odom x={self.odom_x:.4f} dx={self.odom_x - initial_x:.4f}')
        return 0

    def wait_for_odom(self, timeout: float) -> None:
        deadline = time.time() + timeout
        while rclpy.ok() and self.odom_x is None and time.time() < deadline:
            self.get_logger().debug('Waiting for /odom_raw...')
            time.sleep(0.1)


def main() -> None:
    parser = argparse.ArgumentParser(description='JetAuto forward movement probe with odometry feedback.')
    parser.add_argument('--speed', type=float, default=0.15, help='Linear x speed to publish')
    parser.add_argument('--duration', type=float, default=5.0, help='Duration in seconds to publish forward motion')
    parser.add_argument('--hz', type=float, default=10.0, help='Command publish rate')
    args = parser.parse_args()

    rclpy.init()
    node = JetAutoForwardProbe(speed=args.speed, duration=args.duration, publish_hz=args.hz)
    try:
        exit_code = node.run()
    finally:
        node.destroy_node()
        rclpy.shutdown()
    raise SystemExit(exit_code)

if __name__ == '__main__':
    main()
