# JetAuto Cross-Agent Handoff

This file is the handoff point for Claude to continue the JetAuto motion debugging task.

## Current Task

~~Find and fix the active motion control path so the robot moves reliably on this JetAuto setup.~~
**RESOLVED** — direct motor control via `/ros_robot_controller/set_motor` confirmed working.
**Remaining**: confirm the `/controller/cmd_vel` (Twist) path for teleop/joystick use.

## What We Know

- The running robot stack includes `ros_robot_controller`, `controller/odom_publisher`, and `peripherals/joystick_control` — **but `/controller` does not currently appear in `ros2 node list`**, so it may not actually be included in `bringup.launch.py` right now. Needs to be located and confirmed.
- The board serial device is `/dev/rrc`, which is a symlink to `/dev/ttyACM0`.
- The relevant command topics from source are:
  - `/controller/cmd_vel` for chassis motion (not yet confirmed live)
  - `/ros_robot_controller/set_motor` for direct motor commands (**confirmed working**)
- `ros2 node info /ros_robot_controller` confirms `/ros_robot_controller/set_motor` (`ros_robot_controller_msgs/msg/MotorsState`) is a real, unremapped subscription.

## Resolution — Motion Confirmed Working

- Root cause of "robot doesn't move" turned out to be compounded by a separate, confusing issue: the `ros_robot_controller` node launched via `bringup.launch.py` can run as a live process (serial port open, `rclpy.spin()` running, threads idle-not-crashed) while never actually registering on the ROS graph. `ros2 node list` won't show it, and `ros2 daemon stop/start` does **not** fix this — only a full restart of `bringup.launch.py` does.
- **Do not run `ros_robot_controller_node.py` manually as a workaround** — this creates a second process contending for `/dev/ttyACM0` alongside the bringup-managed one and makes the actual state of the system hard to reason about.
- **Confirmed fix**:
```bash
  kill <bringup_pid>
  ros2 launch bringup bringup.launch.py
```
- **Confirmed working test**:
```bash
  ros2 topic pub --once /ros_robot_controller/set_motor \
    ros_robot_controller_msgs/msg/MotorsState "{data: [{id: 1, rps: 1.0}]}"
```
  Wheel moves; `rps: 0.0` stops it.
- Bringup does **not** auto-respawn nodes if they die or are killed — if `ros_robot_controller` (or anything else) ever crashes during real use, someone needs to manually restart bringup.

## Remaining Handoff Instructions for Claude

1. Locate the actual `cmd_vel`→motor translation node (search `ros2_ws/src/driver/controller/` for `cmd_vel` usage).
2. Determine whether it's included in `bringup.launch.py` at all right now — it was not visible in `ros2 node list` during this session.
3. If missing from bringup, either add its launch inclusion or launch it manually alongside bringup (not in place of the motor-level fix above) and re-verify with `ros2 node info`.
4. Once `/controller` (or equivalent) is confirmed live and subscribed to `cmd_vel`, test with a direct `Twist` publish before trying `jetauto_wasd_qe_teleop.py` or joystick control.
5. Separately: `CYCLONEDDS_URI` points to a nonexistent config file (`/etc/cyclonedds/config.xml`) on this machine — worth fixing so DDS behavior isn't relying on silent fallback defaults.

## Useful Files

- `ros2_ws/src/driver/ros_robot_controller/ros_robot_controller/ros_robot_controller_node.py`
- `ros2_ws/src/driver/ros_robot_controller/ros_robot_controller/ros_robot_controller_sdk.py`
- `ros2_ws/src/driver/controller/controller/odom_publisher_node.py` (locate the actual `cmd_vel` translation node — likely nearby)
- `ros2_ws/src/peripherals/peripherals/joystick_control.py`
- `ros2_ws/install/setup.zsh`
- `AIU/JetAuto/scripts/jetauto_forward_probe.py`
- `AIU/JetAuto/scripts/jetauto_direct_motor_probe.py`

## Handoff Priorities

- ~~Priority 1: verify actual live topics and subscriptions for motion control.~~ Done.
- ~~Priority 2: confirm `/dev/rrc` is open by only one process and the serial bridge is healthy.~~ Done — confirmed via a single bringup-managed process.
- ~~Priority 3: execute a simple direct motor probe before adding keyboard or joystick control.~~ Done, confirmed working.
- **New Priority 1**: locate and confirm the `cmd_vel` translation node for higher-level teleop/joystick control.

## Notes

- If `ros_robot_controller` doesn't appear in `ros2 node list` after any future restart, don't assume it's a daemon cache issue — restart the whole bringup process, not just the daemon, and don't manually launch a duplicate node process to "fix" it.
- Keep any future handoff focused on the `cmd_vel` layer next; direct motor control is a solved, repeatable baseline to fall back on for testing.