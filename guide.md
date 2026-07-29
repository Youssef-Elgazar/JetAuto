# JetAuto Guide

This folder is the working notebook for JetAuto lab setup, maintenance, and experiment notes.
Use it to collect what is known, what was verified locally, and what still needs validation on the robot.

Official reference:
- [JetAuto Pi Quick Start Guide](https://wiki.hiwonder.com/projects/JetAutoPi/en/latest/docs/1.quick_start_guide.htm)

## Bringup Command

To start the full robot stack:

```bash
ros2 daemon stop
ros2 daemon start
ros2 launch bringup bringup.launch.py
```

Run this in the foreground (not backgrounded) the first few times you use it, so you can see startup output directly and catch any node failures immediately. **Bringup does not auto-respawn crashed or killed nodes** — if `ros_robot_controller` or anything else dies mid-session, you must stop and re-run this command; there is no supervisor bringing individual nodes back automatically.

To stop it, find its PID and kill it:
```bash
ps aux | grep bringup
kill <bringup_pid>
```

**Do not** run `ros_robot_controller_node.py` (or any other node script) manually as a workaround while bringup is already running — this creates a second process contending for the same serial port (`/dev/ttyACM0`) and makes the system's actual state hard to reason about.

## Known Fix — ros_robot_controller Missing on Some Units

- **Symptom**: `bringup.launch.py` runs clean, every other node comes up (`odom_publisher`, `controller_manager`, cameras, lidar, joystick, etc.), but `ros_robot_controller` never appears in `ros2 node list`. No process in `ps aux`, no logs in `~/.ros/log`. Running the node manually (`ros2 run ros_robot_controller ros_robot_controller`) works fine and stays up.
- **Cause**: `ros_robot_controller.launch.py` defaults the `device` parameter to `'auto'`, which triggers a scan (`/dev/ttyACM0` → `/dev/ttyACM1` → `/dev/ttyUSB0` → `/dev/ttyUSB1` → glob fallback) inside `resolve_device()`. On some units this appears to race against something else grabbing the serial port right at boot/launch time (suspect: ModemManager/brltty auto-probing new ACM/USB serial devices) — the node dies before it ever spins or logs, only when launched through the full bringup chain.
- **Fix**: in `ros2_ws/src/driver/ros_robot_controller/launch/ros_robot_controller.launch.py`, change:
```python
  device = LaunchConfiguration('device', default='auto')
```
  to:
```python
  device = LaunchConfiguration('device', default='/dev/rrc')
```
  Then restart the ROS daemon and relaunch bringup:
```bash
  ros2 daemon stop
  ros2 daemon start
  ros2 launch bringup bringup.launch.py
```
- Confirmed working after this change — `ros_robot_controller` now shows up in `ros2 node list` and stays up.
- **Still worth checking eventually, not yet confirmed**: whether ModemManager/brltty is actually the thing racing for the port (`systemctl status ModemManager`, `systemctl status brltty`), and whether a udev rule (`ENV{ID_MM_DEVICE_IGNORE}="1"`) is a cleaner long-term fix than hardcoding the device path.

## What This Guide Should Contain

- Hardware and wiring notes for each JetAuto variant in the lab.
- ROS 2 launch commands, topics, services, and parameters that were verified here.
- Setup steps for cameras, lidar, controller boards, and servo chains.
- Known-good scripts, demo entry points, and troubleshooting procedures.
- Experiment notes that turn faculty ideas into repeatable lab exercises.
- Validation checklists for TAs and students before handing a robot back into circulation.

## Local Findings So Far

- Bringup is started with `ros2 launch bringup bringup.launch.py` (see above).
- The main app launcher is [ros2_ws/src/app/launch/start_app.launch.py](/home/ubuntu/ros2_ws/src/app/launch/start_app.launch.py).
- The JetAuto camera stack uses [ros2_ws/src/peripherals/launch/depth_camera.launch.py](/home/ubuntu/ros2_ws/src/peripherals/launch/depth_camera.launch.py).
- On JetAuto, the image topic used by the app stack is `/depth_cam/rgb/image_raw`.
- Portable copies of the current test scripts now live in [scripts/](/home/ubuntu/AIU/JetAuto/scripts).
- The camera viewer is [scripts/jetauto_camera_viewer.py](scripts/jetauto_camera_viewer.py).
- The object detector is [scripts/jetauto_object_detector.py](scripts/jetauto_object_detector.py).
- The detector-only variant is [scripts/jetauto_object_detector_only.py](scripts/jetauto_object_detector_only.py).
- The keyboard teleop script is [scripts/jetauto_wasd_qe_teleop.py](scripts/jetauto_wasd_qe_teleop.py).
- The forward motion probe is [scripts/jetauto_forward_test.py](scripts/jetauto_forward_test.py).
- The new reusable probe script is [Scripts/jetauto_forward_probe.py](Scripts/jetauto_forward_probe.py).
- The controller node uses [ros2_ws/src/driver/ros_robot_controller/launch/ros_robot_controller.launch.py](/home/ubuntu/ros2_ws/src/driver/ros_robot_controller/launch/ros_robot_controller.launch.py) and defaults to `/dev/ttyACM0` at 1,000,000 baud.
- Local YOLO weights are available under `/home/ubuntu/third_party/yolo/yolov11/`.

## Motion Debugging — Resolved

- **Root cause**: the `ros_robot_controller` node launched by `bringup.launch.py` can end up alive as a process (holding `/dev/ttyACM0`, spinning in `rclpy.spin()`, no crash) but never register on the ROS graph — `ros2 node list` won't show it even after a `ros2 daemon stop/start`. Likely cause: a long-lived DDS participant losing multicast/discovery state after a network interface change; not fully root-caused, but consistently fixed by a restart.
- **Fix**: restart the whole `bringup.launch.py` process (`kill <bringup_pid>` then re-run `ros2 launch bringup bringup.launch.py`), not just the individual node — bringup does **not** auto-respawn crashed/killed nodes.
- **Do not** start `ros_robot_controller_node.py` manually as a second process while bringup's copy is still running.
- **Verification sequence** after any restart:
```bash
  ros2 node list
  ros2 node info /ros_robot_controller
  ros2 topic pub --once /ros_robot_controller/set_motor \
    ros_robot_controller_msgs/msg/MotorsState "{data: [{id: 1, rps: 1.0}]}"
```
  `rps: 0.0` stops the motor. Confirmed working end-to-end.
- `ros2 node info /ros_robot_controller` confirms `/ros_robot_controller/set_motor` is a real, unremapped subscriber (`ros_robot_controller_msgs/msg/MotorsState`) — no topic-naming issue.
- **Open gap**: `controller.launch.py` (which provides `odom_publisher_node.py`, the actual `/controller/cmd_vel` subscriber) is **confirmed not included** in `bringup.launch.py`. This is why `cmd_vel`-based scripts (`jetauto_forward_probe.py`, `jetauto_wasd_qe_teleop.py`, joystick control) won't move the robot yet — there's no live subscriber on that topic. Next: launch [ros2_ws/src/driver/controller/launch/controller.launch.py](/home/ubuntu/ros2_ws/src/driver/controller/launch/controller.launch.py) alongside bringup, or add it into bringup's includes, then re-test.
- **Known loose end**: `CYCLONEDDS_URI` is set to `file:///etc/cyclonedds/config.xml` on this machine, but that file does not exist anywhere on disk — Cyclone is silently falling back to defaults. Not confirmed as the cause of the discovery issue above, but worth cleaning up (either point the URI correctly or remove it) so DDS behavior is deterministic.

## Suggested Lab Workflow

1. Run `ros2 launch bringup bringup.launch.py` to start the robot stack.
2. Confirm the robot variant and camera launch path.
3. Verify the camera stream with a minimal viewer.
4. Verify object detection on the live stream.
5. Verify the controller and serial stack before trying motion scripts (`ros2 node list` / `ros2 node info /ros_robot_controller`).
6. Record the exact topic names, model path, and launch steps that worked.
7. Turn the result into a short lab handout or TA checklist.

## Useful Notes To Add Later

- Serial numbers and hardware revisions.
- Which USB cameras, depth cameras, and lidar units are installed.
- Calibration values, camera intrinsics, and servo offsets.
- Recovery steps for common startup failures.
- Course-specific experiment instructions and grading notes.