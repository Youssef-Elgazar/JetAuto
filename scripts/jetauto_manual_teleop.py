#!/usr/bin/env python3

import select
import sys
import termios
import time
import tty

import rclpy
from geometry_msgs.msg import Twist
from rclpy.node import Node

HELP_TEXT = """
JetAuto manual teleop
-----------------------
W/S: forward / backward
A/D: strafe left / right
Q/E: rotate left / right
Space: stop
Ctrl-C: quit
"""

class ManualTeleop(Node):
    def __init__(self):
        super().__init__('jetauto_manual_teleop')
        self.publisher = self.create_publisher(Twist, '/controller/cmd_vel', 1)
        self.linear_step = 0.18
        self.strafe_step = 0.16
        self.angular_step = 0.8
        self._settings = termios.tcgetattr(sys.stdin)
        self.current_twist = Twist()

    def get_key(self) -> str:
        tty.setraw(sys.stdin.fileno())
        ready, _, _ = select.select([sys.stdin], [], [], 0.1)
        key = sys.stdin.read(1) if ready else ''
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self._settings)
        return key

    def publish_twist(self, twist: Twist) -> None:
        self.publisher.publish(twist)

    def stop(self) -> None:
        self.current_twist = Twist()
        self.publish_twist(self.current_twist)

    def run(self) -> None:
        print(HELP_TEXT)
        try:
            while rclpy.ok():
                key = self.get_key()
                if key == 'w':
                    self.current_twist.linear.x = self.linear_step
                    self.current_twist.linear.y = 0.0
                    self.current_twist.angular.z = 0.0
                elif key == 's':
                    self.current_twist.linear.x = -self.linear_step
                    self.current_twist.linear.y = 0.0
                    self.current_twist.angular.z = 0.0
                elif key == 'a':
                    self.current_twist.linear.x = 0.0
                    self.current_twist.linear.y = self.strafe_step
                    self.current_twist.angular.z = 0.0
                elif key == 'd':
                    self.current_twist.linear.x = 0.0
                    self.current_twist.linear.y = -self.strafe_step
                    self.current_twist.angular.z = 0.0
                elif key == 'q':
                    self.current_twist.linear.x = 0.0
                    self.current_twist.linear.y = 0.0
                    self.current_twist.angular.z = self.angular_step
                elif key == 'e':
                    self.current_twist.linear.x = 0.0
                    self.current_twist.linear.y = 0.0
                    self.current_twist.angular.z = -self.angular_step
                elif key == ' ':  # stop
                    self.stop()
                elif key == '\x03':  # Ctrl-C
                    break

                self.publish_twist(self.current_twist)
                time.sleep(0.05)
        finally:
            self.stop()
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self._settings)


def main() -> None:
    rclpy.init()
    node = ManualTeleop()
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
