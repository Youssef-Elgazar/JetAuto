# JetAuto Guide

This folder is the working notebook for JetAuto lab setup, maintenance, and experiment notes.
Use it to collect what is known, what was verified locally, and what still needs validation on the robot.

Official reference:
- [JetAuto Pi Quick Start Guide](https://wiki.hiwonder.com/projects/JetAutoPi/en/latest/docs/1.quick_start_guide.htm)

## What This Guide Should Contain

- Hardware and wiring notes for each JetAuto variant in the lab.
- ROS 2 launch commands, topics, services, and parameters that were verified here.
- Setup steps for cameras, lidar, controller boards, and servo chains.
- Known-good scripts, demo entry points, and troubleshooting procedures.
- Experiment notes that turn faculty ideas into repeatable lab exercises.
- Validation checklists for TAs and students before handing a robot back into circulation.

## Local Findings So Far

- The main app launcher is [ros2_ws/src/app/launch/start_app.launch.py](/home/ubuntu/ros2_ws/src/app/launch/start_app.launch.py).
- The JetAuto camera stack uses [ros2_ws/src/peripherals/launch/depth_camera.launch.py](/home/ubuntu/ros2_ws/src/peripherals/launch/depth_camera.launch.py).
- On JetAuto, the image topic used by the app stack is `/depth_cam/rgb/image_raw`.
- Portable copies of the current test scripts now live in [scripts/](/home/ubuntu/AIU/JetAuto/scripts).
- The camera viewer is [scripts/jetauto_camera_viewer.py](scripts/jetauto_camera_viewer.py).
- The object detector is [scripts/jetauto_object_detector.py](scripts/jetauto_object_detector.py).
- The detector-only variant is [scripts/jetauto_object_detector_only.py](scripts/jetauto_object_detector_only.py).
- The keyboard teleop script is [scripts/jetauto_wasd_qe_teleop.py](scripts/jetauto_wasd_qe_teleop.py).
- The forward motion probe is [scripts/jetauto_forward_test.py](scripts/jetauto_forward_test.py).
- The most important current finding is that motion still did not work because the controller path appears unhealthy.
- Earlier logs showed `ros_robot_controller` failing with a serial read exception, which is the first thing to fix before iterating on teleop or obstacle avoidance.
- Local YOLO weights are available under `/home/ubuntu/third_party/yolo/yolov11/`.

## Suggested Lab Workflow

1. Confirm the robot variant and camera launch path.
2. Verify the camera stream with a minimal viewer.
3. Verify object detection on the live stream.
4. Verify the controller and serial stack before trying motion scripts.
5. Record the exact topic names, model path, and launch steps that worked.
6. Turn the result into a short lab handout or TA checklist.

## Useful Notes To Add Later

- Serial numbers and hardware revisions.
- Which USB cameras, depth cameras, and lidar units are installed.
- Calibration values, camera intrinsics, and servo offsets.
- Recovery steps for common startup failures.
- Course-specific experiment instructions and grading notes.
