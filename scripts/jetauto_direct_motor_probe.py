#!/usr/bin/env python3

import argparse
import math
import time

import rclpy
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from ros_robot_controller_msgs.msg import MotorState, MotorsState, BuzzerState
from rclpy.node import Node

class JetAutoDirectMotorProbe(Node):
    def __init__(self, speed=0.2, duration=4.0, use_direct=True, use_cmd_vel=False):
        super().__init__('jetauto_direct_motor_probe')
        self.speed = speed
        self.duration = duration
        self.use_direct = use_direct
        self.use_cmd_vel = use_cmd_vel
        self.odom_x = None
        self.odom_y = None

        self.buzzer_pub = self.create_publisher(BuzzerState, '/ros_robot_controller/set_buzzer', 1)
        if self.use_cmd_vel:
            self.cmd_vel_pub = self.create_publisher(Twist, '/controller/cmd_vel', 1)
        if self.use_direct:
            self.motor_pub = self.create_publisher(MotorsState, '/ros_robot_controller/set_motor', 1)
        self.odom_sub = self.create_subscription(Odometry, '/odom_raw', self.odom_callback, 10)
        self.create_timer(0.1, lambda: None)

    def odom_callback(self, msg: Odometry) -> None:
        self.odom_x = msg.pose.pose.position.x
        self.odom_y = msg.pose.pose.position.y

    @staticmethod
    def twist_to_motors(linear_x: float, linear_y: float, angular_z: float):
        wheelbase = 0.216
        track_width = 0.195
        wheel_diameter = 0.097
        motor1 = (linear_x - linear_y - angular_z * (wheelbase + track_width) / 2)
        motor2 = (linear_x + linear_y - angular_z * (wheelbase + track_width) / 2)
        motor3 = (linear_x + linear_y + angular_z * (wheelbase + track_width) / 2)
        motor4 = (linear_x - linear_y + angular_z * (wheelbase + track_width) / 2)
        def speed_to_rps(speed):
            return speed / (math.pi * wheel_diameter)
        values = [speed_to_rps(v) for v in [motor1, motor2, -motor3, -motor4]]
        msg = MotorsState()
        msg.data = [MotorState(id=i + 1, rps=float(values[i])) for i in range(4)]
        return msg

    def publish_buzzer(self) -> None:
        msg = BuzzerState()
        msg.freq = 1900
        msg.on_time = 0.1
        msg.off_time = 0.05
        msg.repeat = 1
        self.buzzer_pub.publish(msg)

    def run(self) -> int:
        self.get_logger().info('Starting direct motor probe')
        self.publish_buzzer()
        start = time.time()
        timeout = start + 3.0
        while rclpy.ok() and self.odom_x is None and time.time() < timeout:
            self.get_logger().info('Waiting for /odom_raw updates...')
            time.sleep(0.2)

        if self.odom_x is None:
            self.get_logger().warn('No odometry yet, continuing anyway')
            initial_x = 0.0
            initial_y = 0.0
        else:
            initial_x = self.odom_x
            initial_y = self.odom_y

        move_twist = Twist()
        move_twist.linear.x = self.speed
        move_twist.linear.y = 0.0
        move_twist.angular.z = 0.0

        if self.use_direct:
            motor_cmd = self.twist_to_motors(move_twist.linear.x, move_twist.linear.y, move_twist.angular.z)
            self.get_logger().info(f'Publishing direct motor command: {motor_cmd.data[0].rps:.3f} rps etc.')
        if self.use_cmd_vel:
            self.get_logger().info('Publishing /controller/cmd_vel alongside direct motor command')

        end_time = time.time() + self.duration
        while rclpy.ok() and time.time() < end_time:
            if self.use_direct:
                self.motor_pub.publish(motor_cmd)
            if self.use_cmd_vel:
                self.cmd_vel_pub.publish(move_twist)
            if self.odom_x is not None:
                dx = self.odom_x - initial_x
                dy = self.odom_y - initial_y
                self.get_logger().info(f'odom x={self.odom_x:.4f} dx={dx:.4f} y={self.odom_y:.4f} dy={dy:.4f}')
            else:
                self.get_logger().info('No odometry yet')
            time.sleep(0.2)

        self.get_logger().info('Stopping motors')
        if self.use_direct:
            stop_msg = MotorsState()
            stop_msg.data = [MotorState(id=i + 1, rps=0.0) for i in range(4)]
            self.motor_pub.publish(stop_msg)
        if self.use_cmd_vel:
            self.cmd_vel_pub.publish(Twist())
        self.get_logger().info('Probe complete')
        return 0


def main() -> None:
    parser = argparse.ArgumentParser(description='JetAuto direct motor probe.')
    parser.add_argument('--speed', type=float, default=0.2, help='Forward speed in m/s')
    parser.add_argument('--duration', type=float, default=4.0, help='Duration in seconds')
    parser.add_argument('--no-direct', dest='use_direct', action='store_false', help='Do not publish direct motor commands')
    parser.add_argument('--cmd-vel', dest='use_cmd_vel', action='store_true', help='Also publish to /controller/cmd_vel')
    args = parser.parse_args()

    rclpy.init()
    node = JetAutoDirectMotorProbe(speed=args.speed, duration=args.duration, use_direct=args.use_direct, use_cmd_vel=args.use_cmd_vel)
    try:
        node.run()
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
