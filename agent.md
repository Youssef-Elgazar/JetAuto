# JetAuto Cross-Agent Handoff

Use this file as the handoff point between sessions and devices when working on JetAuto.

## Current Goal

Get the robot moving reliably before building more features.

## What Has Been Verified

- Camera viewing works with `/depth_cam/rgb/image_raw` on JetAuto.
- Object detection scripts run from the Desktop.
- The user wanted the repo to collect the scripts in a `scripts/` folder.

## Current Blocker

- Motion did not work.
- The strongest evidence so far points to the hardware/controller path rather than the keyboard teleop logic.
- Earlier logs showed `ros_robot_controller` throwing a serial exception: `device reports readiness to read but returned no data (device disconnected or multiple access on port?)`.

## Useful Files

- [guide.md](guide.md)
- [map.md](map.md)
- [scripts/jetauto_camera_viewer.py](scripts/jetauto_camera_viewer.py)
- [scripts/jetauto_object_detector.py](scripts/jetauto_object_detector.py)
- [scripts/jetauto_object_detector_only.py](scripts/jetauto_object_detector_only.py)
- [scripts/jetauto_wasd_qe_teleop.py](scripts/jetauto_wasd_qe_teleop.py)
- [scripts/jetauto_forward_test.py](scripts/jetauto_forward_test.py)

## Known Working Assumptions

- JetAuto camera topic: `/depth_cam/rgb/image_raw`
- Motion topic used by app/control scripts: `/controller/cmd_vel`
- Lidar topic used by the app stack: `/scan_raw` and filtered `/scan`

## Next Checks

1. Confirm only one process opens the robot serial device.
2. Confirm the controller stack stays up without serial exceptions.
3. Test a constant forward `Twist` before adding any keyboard or avoidance logic.

## Session Notes

- Keep changes small and local.
- Preserve Desktop scripts as portable test artifacts.
- If a script appears to do nothing, check the robot stack health first.