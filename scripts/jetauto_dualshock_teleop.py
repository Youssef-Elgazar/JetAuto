#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Joy
from geometry_msgs.msg import Twist

AXES_MAP = ('lx', 'ly', 'rx', 'ry', 'r2', 'l2', 'hat_x', 'hat_y')

class JetAutoDualShockTeleop(Node):
    def __init__(self):
        super().__init__('jetauto_dualshock_teleop')
        self.declare_parameter('joy_topic', '/ros_robot_controller/joy')
        self.declare_parameter('cmd_vel_topic', '/controller/cmd_vel')
        self.declare_parameter('max_linear', 0.7)
        self.declare_parameter('max_angular', 3.0)
        self.declare_parameter('deadzone', 0.1)

        joy_topic = self.get_parameter('joy_topic').value
        cmd_vel_topic = self.get_parameter('cmd_vel_topic').value
        self.max_linear = self.get_parameter('max_linear').value
        self.max_angular = self.get_parameter('max_angular').value
        self.deadzone = self.get_parameter('deadzone').value

        self.get_logger().info(f'Listening for DualShock data on: {joy_topic}')
        self.get_logger().info(f'Publishing movement commands to: {cmd_vel_topic}')

        self.publisher = self.create_publisher(Twist, cmd_vel_topic, 1)
        self.subscription = self.create_subscription(Joy, joy_topic, self.joy_callback, 1)

    @staticmethod
    def apply_deadzone(value: float, threshold: float) -> float:
        return 0.0 if abs(value) < threshold else value

    def joy_callback(self, msg: Joy) -> None:
        if len(msg.axes) < 4:
            self.get_logger().warning('Joy message has fewer than 4 axes, skipping')
            return

        axes = dict(zip(AXES_MAP, list(msg.axes)[: len(AXES_MAP)]))
        twist = Twist()
        twist.linear.y = self.max_linear * self.apply_deadzone(axes.get('lx', 0.0), self.deadzone)
        twist.linear.x = self.max_linear * self.apply_deadzone(axes.get('ly', 0.0), self.deadzone)
        twist.angular.z = self.max_angular * self.apply_deadzone(axes.get('rx', 0.0), self.deadzone)
        self.publisher.publish(twist)

        self.get_logger().debug(f'joy axes={axes} -> twist x={twist.linear.x:.3f} y={twist.linear.y:.3f} z={twist.angular.z:.3f}')


def main():
    rclpy.init()
    node = JetAutoDualShockTeleop()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
