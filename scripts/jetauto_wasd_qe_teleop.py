#!/usr/bin/env python3

import os
import select
import sys
import termios
import time
import tty

import rclpy
from geometry_msgs.msg import Twist
from rclpy.node import Node


HELP_TEXT = """
JetAuto keyboard teleop
-----------------------
W/S: forward / backward
A/D: strafe left / right
Q/E: rotate left / right
Space: stop
Ctrl-C: quit
"""


class KeyboardTeleop(Node):
    def __init__(self):
        super().__init__('jetauto_wasd_qe_teleop')
        self.publisher = self.create_publisher(Twist, '/controller/cmd_vel', 1)
        self.linear_step = 0.18
        self.strafe_step = 0.16
        self.angular_step = 0.8
        self.publish_hz = 20.0
        self.idle_timeout = 0.35
        self._settings = termios.tcgetattr(sys.stdin)

    def get_key(self) -> str:
        tty.setraw(sys.stdin.fileno())
        ready, _, _ = select.select([sys.stdin], [], [], 0.1)
        key = sys.stdin.read(1) if ready else ''
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self._settings)
        return key

    def publish_twist(self, linear_x=0.0, linear_y=0.0, angular_z=0.0) -> None:
        twist = Twist()
        twist.linear.x = linear_x
        twist.linear.y = linear_y
        twist.angular.z = angular_z
        self.publisher.publish(twist)

    def run(self) -> None:
        print(HELP_TEXT)
        current_twist = Twist()
        last_key_time = 0.0
        loop_delay = 1.0 / self.publish_hz
        try:
            while rclpy.ok():
                key = self.get_key()
                now = time.time()

                if key == 'w':
                    current_twist.linear.x = self.linear_step
                    current_twist.linear.y = 0.0
                    current_twist.angular.z = 0.0
                    last_key_time = now
                elif key == 's':
                    current_twist.linear.x = -self.linear_step
                    current_twist.linear.y = 0.0
                    current_twist.angular.z = 0.0
                    last_key_time = now
                elif key == 'a':
                    current_twist.linear.x = 0.0
                    current_twist.linear.y = self.strafe_step
                    current_twist.angular.z = 0.0
                    last_key_time = now
                elif key == 'd':
                    current_twist.linear.x = 0.0
                    current_twist.linear.y = -self.strafe_step
                    current_twist.angular.z = 0.0
                    last_key_time = now
                elif key == 'q':
                    current_twist.linear.x = 0.0
                    current_twist.linear.y = 0.0
                    current_twist.angular.z = self.angular_step
                    last_key_time = now
                elif key == 'e':
                    current_twist.linear.x = 0.0
                    current_twist.linear.y = 0.0
                    current_twist.angular.z = -self.angular_step
                    last_key_time = now
                elif key == ' ':
                    current_twist = Twist()
                    last_key_time = 0.0
                elif key == '\x03':
                    break

                if last_key_time and now - last_key_time > self.idle_timeout:
                    current_twist = Twist()
                    last_key_time = 0.0

                self.publisher.publish(current_twist)
                if key == 'w':
                    print('forward')
                elif key == 's':
                    print('backward')
                elif key == 'a':
                    print('left')
                elif key == 'd':
                    print('right')
                elif key == 'q':
                    print('turn left')
                elif key == 'e':
                    print('turn right')
                elif key == ' ':
                    print('stop')

                time.sleep(loop_delay)
        finally:
            self.publish_twist()
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self._settings)


def main() -> None:
    rclpy.init()
    node = KeyboardTeleop()
    try:
        node.run()
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()