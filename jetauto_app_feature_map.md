# Jetauto App Feature Map

This file captures the Python entry points I found while crawling the home directory for Jetauto app features.

## Core ROS2 app

The main app launcher is [ros2_ws/src/app/launch/start_app.launch.py](/home/ubuntu/ros2_ws/src/app/launch/start_app.launch.py). It includes the primary feature nodes in [ros2_ws/src/app/app/](/home/ubuntu/ros2_ws/src/app/app):

| Feature | Main Python script | Notes |
|---|---|---|
| Lidar / sensor support | [ros2_ws/src/app/app/lidar_controller.py](/home/ubuntu/ros2_ws/src/app/app/lidar_controller.py) | Shared sensing/control node used by the app launch |
| Line following | [ros2_ws/src/app/app/line_following.py](/home/ubuntu/ros2_ws/src/app/app/line_following.py) | Vision + lidar based line tracking |
| Object tracking | [ros2_ws/src/app/app/object_tracking.py](/home/ubuntu/ros2_ws/src/app/app/object_tracking.py) | Color-based target following |
| AR overlay | [ros2_ws/src/app/app/ar_app.py](/home/ubuntu/ros2_ws/src/app/app/ar_app.py) | AprilTag / model overlay app |
| Patrol modes | [ros2_ws/src/app/app/patrol.py](/home/ubuntu/ros2_ws/src/app/app/patrol.py) | Rectangle / triangle / circle / parallelogram motion |

## ROS Wiring Pass

This pass traces the ROS launch files and runtime interfaces that the app menu uses.

| Feature | Launch file | Main ROS publishers / subscribers / services |
|---|---|---|
| Lidar / sensor support | [ros2_ws/src/app/launch/lidar_node.launch.py](/home/ubuntu/ros2_ws/src/app/launch/lidar_node.launch.py) | Publishes `/controller/cmd_vel` and `servo_controller`; subscribes to `/scan_raw`; exposes `~/enter`, `~/exit`, `~/set_running`, `~/set_param`, `~/init_finish` |
| Line following | [ros2_ws/src/app/launch/line_following_node.launch.py](/home/ubuntu/ros2_ws/src/app/launch/line_following_node.launch.py) | Publishes `/controller/cmd_vel`, `servo_controller`, and `~/image_result`; subscribes to `/scan_raw`, `/depth_cam/rgb/image_raw`, or `/usb_cam/image_raw`; exposes `~/enter`, `~/exit`, `~/set_running`, `~/set_color`, `~/set_target_color`, `~/get_target_color`, `~/set_threshold`, `~/init_finish` |
| Object tracking | [ros2_ws/src/app/launch/object_tracking_node.launch.py](/home/ubuntu/ros2_ws/src/app/launch/object_tracking_node.launch.py) | Publishes `/controller/cmd_vel`, `servo_controller`, and `~/image_result`; subscribes to `/depth_cam/rgb/image_raw` or `/usb_cam/image_raw`; exposes `~/enter`, `~/exit`, `~/set_running`, `~/set_color`, `~/set_target_color`, `~/get_target_color`, `~/set_threshold`, `~/init_finish` |
| AR overlay | [ros2_ws/src/app/launch/ar_app_node.launch.py](/home/ubuntu/ros2_ws/src/app/launch/ar_app_node.launch.py) | Publishes `~/image_result`; subscribes to `/depth_cam/rgb/image_raw` or `/usb_cam/image_raw` and `/depth_cam/rgb/camera_info`; exposes `~/enter`, `~/exit`, `~/set_model`, `~/init_finish` |
| Patrol modes | [ros2_ws/src/app/launch/patrol_node.launch.py](/home/ubuntu/ros2_ws/src/app/launch/patrol_node.launch.py) | Publishes `/controller/cmd_vel`; exposes `~/enter`, `~/exit`, `~/set_running`, `~/init_finish` |

### Common launch dependencies

- [ros2_ws/src/peripherals/launch/lidar.launch.py](/home/ubuntu/ros2_ws/src/peripherals/launch/lidar.launch.py) provides the lidar input used by line following and lidar control.
- [ros2_ws/src/peripherals/launch/depth_camera.launch.py](/home/ubuntu/ros2_ws/src/peripherals/launch/depth_camera.launch.py) provides the RGB camera input used by line following, object tracking, and AR.
- [ros2_ws/src/driver/controller/launch/controller.launch.py](/home/ubuntu/ros2_ws/src/driver/controller/launch/controller.launch.py) provides the chassis controller used by the app nodes that publish `/controller/cmd_vel`.

## Related app-style feature packages

These folders contain higher-level demo logic that looks useful when building a custom app.

| Area | Main Python scripts | Notes |
|---|---|---|
| Color sorting | [ros2_ws/src/large_models_examples/large_models_examples/color_sorting/object_sorting.py](/home/ubuntu/ros2_ws/src/large_models_examples/large_models_examples/color_sorting/object_sorting.py), [ros2_ws/src/large_models_examples/large_models_examples/color_sorting/llm_object_sorting.py](/home/ubuntu/ros2_ws/src/large_models_examples/large_models_examples/color_sorting/llm_object_sorting.py) | Vision-based sorting and LLM-assisted variant |
| Navigation transport | [ros2_ws/src/large_models_examples/large_models_examples/navigation_transport/navigation_transport.py](/home/ubuntu/ros2_ws/src/large_models_examples/large_models_examples/navigation_transport/navigation_transport.py), [ros2_ws/src/large_models_examples/large_models_examples/navigation_transport/automatic_pick.py](/home/ubuntu/ros2_ws/src/large_models_examples/large_models_examples/navigation_transport/automatic_pick.py), [ros2_ws/src/large_models_examples/large_models_examples/navigation_transport/vllm_navigation_transport.py](/home/ubuntu/ros2_ws/src/large_models_examples/large_models_examples/navigation_transport/vllm_navigation_transport.py) | Navigation + pick/place workflow |
| Object transport | [ros2_ws/src/large_models_examples/large_models_examples/object_transport/object_transport.py](/home/ubuntu/ros2_ws/src/large_models_examples/large_models_examples/object_transport/object_transport.py), [ros2_ws/src/large_models_examples/large_models_examples/object_transport/vllm_object_transport.py](/home/ubuntu/ros2_ws/src/large_models_examples/large_models_examples/object_transport/vllm_object_transport.py) | Transport behavior stack |
| Waste classification | [ros2_ws/src/large_models_examples/large_models_examples/waste_classification/waste_classification.py](/home/ubuntu/ros2_ws/src/large_models_examples/large_models_examples/waste_classification/waste_classification.py), [ros2_ws/src/large_models_examples/large_models_examples/waste_classification/llm_waste_classification.py](/home/ubuntu/ros2_ws/src/large_models_examples/large_models_examples/waste_classification/llm_waste_classification.py) | Sorting/classification demo |
| Visual patrol / tracking | [ros2_ws/src/large_models_examples/large_models_examples/llm_visual_patrol.py](/home/ubuntu/ros2_ws/src/large_models_examples/large_models_examples/llm_visual_patrol.py), [ros2_ws/src/large_models_examples/large_models_examples/llm_color_track.py](/home/ubuntu/ros2_ws/src/large_models_examples/large_models_examples/llm_color_track.py), [ros2_ws/src/large_models_examples/large_models_examples/tracker.py](/home/ubuntu/ros2_ws/src/large_models_examples/large_models_examples/tracker.py), [ros2_ws/src/large_models_examples/large_models_examples/track_anything.py](/home/ubuntu/ros2_ws/src/large_models_examples/large_models_examples/track_anything.py) | Tracking and patrol logic |
| Navigation / LLM control | [ros2_ws/src/large_models_examples/large_models_examples/vllm_navigation.py](/home/ubuntu/ros2_ws/src/large_models_examples/large_models_examples/vllm_navigation.py), [ros2_ws/src/large_models_examples/large_models_examples/llm_control_move.py](/home/ubuntu/ros2_ws/src/large_models_examples/large_models_examples/llm_control_move.py) | Navigation and move control |
| Road network tools | [ros2_ws/src/large_models_examples/large_models_examples/road_network/road_network_builder.py](/home/ubuntu/ros2_ws/src/large_models_examples/large_models_examples/road_network/road_network_builder.py), [ros2_ws/src/large_models_examples/large_models_examples/road_network/road_network_navigator.py](/home/ubuntu/ros2_ws/src/large_models_examples/large_models_examples/road_network/road_network_navigator.py), [ros2_ws/src/large_models_examples/large_models_examples/road_network/nav2_execution_node.py](/home/ubuntu/ros2_ws/src/large_models_examples/large_models_examples/road_network/nav2_execution_node.py) | Map/network navigation tooling |
| Voice control | [ros2_ws/src/xf_mic_asr_offline/scripts/voice_control_move.py](/home/ubuntu/ros2_ws/src/xf_mic_asr_offline/scripts/voice_control_move.py), [ros2_ws/src/xf_mic_asr_offline/scripts/voice_control_navigation.py](/home/ubuntu/ros2_ws/src/xf_mic_asr_offline/scripts/voice_control_navigation.py), [ros2_ws/src/xf_mic_asr_offline/scripts/voice_control_navigation_transport.py](/home/ubuntu/ros2_ws/src/xf_mic_asr_offline/scripts/voice_control_navigation_transport.py), [ros2_ws/src/xf_mic_asr_offline/scripts/voice_control_color_sorting.py](/home/ubuntu/ros2_ws/src/xf_mic_asr_offline/scripts/voice_control_color_sorting.py), [ros2_ws/src/xf_mic_asr_offline/scripts/voice_control_color_track.py](/home/ubuntu/ros2_ws/src/xf_mic_asr_offline/scripts/voice_control_color_track.py), [ros2_ws/src/xf_mic_asr_offline/scripts/voice_control_arm.py](/home/ubuntu/ros2_ws/src/xf_mic_asr_offline/scripts/voice_control_arm.py) | Speech-driven variants of app behaviors |

## Supporting infrastructure

These are mostly lower-level drivers and peripherals rather than app features themselves:

- [ros2_ws/src/driver/](/home/ubuntu/ros2_ws/src/driver)
- [ros2_ws/src/peripherals/](/home/ubuntu/ros2_ws/src/peripherals)
- [ros2_ws/src/large_models_examples/large_models_examples/function_calling/](/home/ubuntu/ros2_ws/src/large_models_examples/large_models_examples/function_calling)

## ROS Trace Pass

### Large models examples

| Feature script | Launch file | Observed ROS interfaces |
|---|---|---|
| Color sorting | [ros2_ws/src/large_models_examples/large_models_examples/color_sorting/object_sorting_node.launch.py](/home/ubuntu/ros2_ws/src/large_models_examples/large_models_examples/color_sorting/object_sorting_node.launch.py) | Publishes `servo_controller` and `~/image_result`; subscribes to camera images; services include `~/enter`, `~/exit`, `~/enable_sorting`, `~/set_target`, `~/init_finish` |
| LLM color sorting | [ros2_ws/src/large_models_examples/large_models_examples/color_sorting/llm_object_sorting.launch.py](/home/ubuntu/ros2_ws/src/large_models_examples/large_models_examples/color_sorting/llm_object_sorting.launch.py) | Uses the color sorting node plus `large_models` LLM stack; `llm_object_sorting.py` publishes `tts_node/tts_text`, subscribes to `agent_process/result`, `tts_node/play_finish`, `vocal_detect/wakeup`, and exposes `~/init_finish` |
| Object transport | [ros2_ws/src/large_models_examples/large_models_examples/object_transport/object_transport_node.launch.py](/home/ubuntu/ros2_ws/src/large_models_examples/large_models_examples/object_transport/object_transport_node.launch.py) | Publishes `servo_controller`, `~/transport_finished`, and `~/image_result`; services include `~/enter`, `~/exit`, `~/enable_transport`, `~/set_pick_position`, `~/set_place_position`, `~/record_position`, `~/init_finish` |
| LLM object transport | [ros2_ws/src/large_models_examples/large_models_examples/object_transport/vllm_object_transport.launch.py](/home/ubuntu/ros2_ws/src/large_models_examples/large_models_examples/object_transport/vllm_object_transport.launch.py) | Adds `vllm_object_transport.py`, which publishes `tts_node/tts_text` and `/vocal_detect/asr_result`, subscribes to `agent_process/result` and `object_transport/transport_finished`, and exposes `~/init_finish` |
| Navigation transport | [ros2_ws/src/large_models_examples/large_models_examples/navigation_transport/navigation_transport.launch.py](/home/ubuntu/ros2_ws/src/large_models_examples/large_models_examples/navigation_transport/navigation_transport.launch.py) | Brings up `automatic_pick.py`, `navigation_controller.py`, and navigation; the pick node publishes `/servo_controller`, `/controller/cmd_vel`, `~/image_result`, `~/action_finish`, and services `~/pick`, `~/place`, `~/set_target_color`, `~/set_box` |
| LLM navigation transport | [ros2_ws/src/large_models_examples/large_models_examples/navigation_transport/vllm_navigation_transport.launch.py](/home/ubuntu/ros2_ws/src/large_models_examples/large_models_examples/navigation_transport/vllm_navigation_transport.launch.py) | `vllm_navigation_transport.py` subscribes to `usb_cam/image_raw`, `agent_process/result`, `vocal_detect/wakeup`, `tts_node/play_finish`, `navigation_controller/reach_goal`, `automatic_pick/action_finish`, and publishes `tts_node/tts_text` |
| Waste classification | [ros2_ws/src/large_models_examples/large_models_examples/waste_classification/waste_classification.launch.py](/home/ubuntu/ros2_ws/src/large_models_examples/large_models_examples/waste_classification/waste_classification.launch.py) | Publishes `servo_controller` and `~/image_result`; subscribes to `yolo/object_image` and `/usb_cam/camera_info`; services include `~/enter`, `~/exit`, `~/enable_transport`, `~/set_target`, `~/init_finish` |
| LLM waste classification | [ros2_ws/src/large_models_examples/large_models_examples/waste_classification/llm_waste_classification.launch.py](/home/ubuntu/ros2_ws/src/large_models_examples/large_models_examples/waste_classification/llm_waste_classification.launch.py) | `llm_waste_classification.py` publishes `tts_node/tts_text`, subscribes to `agent_process/result`, `tts_node/play_finish`, `vocal_detect/wakeup`, and exposes `~/init_finish` |
| Visual patrol | [ros2_ws/src/large_models_examples/large_models_examples/llm_visual_patrol.launch.py](/home/ubuntu/ros2_ws/src/large_models_examples/large_models_examples/llm_visual_patrol.launch.py) | `llm_visual_patrol.py` uses `tts_node/tts_text`, `agent_process/result`, `vocal_detect/wakeup`, `tts_node/play_finish`, and `~/init_finish` |
| Color tracking | [ros2_ws/src/large_models_examples/large_models_examples/llm_color_track.launch.py](/home/ubuntu/ros2_ws/src/large_models_examples/large_models_examples/llm_color_track.launch.py) | `llm_color_track.py` uses `tts_node/tts_text`, `agent_process/result`, `vocal_detect/wakeup`, `tts_node/play_finish`, and `~/init_finish` |
| Navigation | [ros2_ws/src/large_models_examples/large_models_examples/vllm_navigation.launch.py](/home/ubuntu/ros2_ws/src/large_models_examples/large_models_examples/vllm_navigation.launch.py) | `vllm_navigation.py` publishes `tts_node/tts_text`, subscribes to `agent_process/result`, `vocal_detect/wakeup`, `tts_node/play_finish`, `navigation_controller/reach_goal`, and exposes `~/init_finish` |
| Camera demo | [ros2_ws/src/large_models_examples/large_models_examples/vllm_with_camera.launch.py](/home/ubuntu/ros2_ws/src/large_models_examples/large_models_examples/vllm_with_camera.launch.py) | `vllm_with_camera.py` publishes `servo_controller` and `tts_node/tts_text`, subscribes to a camera topic, `agent_process/result`, `tts_node/play_finish`, and exposes `~/init_finish` |
| Track arm | [ros2_ws/src/large_models_examples/large_models_examples/vllm_track_arm/vllm_track_arm.launch.py](/home/ubuntu/ros2_ws/src/large_models_examples/large_models_examples/vllm_track_arm/vllm_track_arm.launch.py) | `vllm_track_arm.py` publishes `servo_controller`, `/controller/cmd_vel`, `tts_node/tts_text`, subscribes to `tts_node/play_finish`, `agent_process/result`, `vocal_detect/wakeup`, a camera image topic, and services `~/start_arm_track`, `~/stop_arm_track`, `~/init_finish` |
| Track object | [ros2_ws/src/large_models_examples/large_models_examples/vllm_track.launch.py](/home/ubuntu/ros2_ws/src/large_models_examples/large_models_examples/vllm_track.launch.py) | `vllm_track.py` publishes `servo_controller`, `/controller/cmd_vel`, `tts_node/tts_text`, subscribes to `tts_node/play_finish`, `agent_process/result`, `vocal_detect/wakeup`, and exposes `~/init_finish` |

### Function calling and LLM control

| Feature script | Launch file | Observed ROS interfaces |
|---|---|---|
| Generic LLM control | [ros2_ws/src/large_models_examples/large_models_examples/function_calling/llm_control_progress.launch.py](/home/ubuntu/ros2_ws/src/large_models_examples/large_models_examples/function_calling/llm_control_progress.launch.py) | Starts controller, depth camera, lidar, line following or navigation depending on mode, and `llm_control.py`; `llm_control.py` uses `agent_process/tools`, `agent_process/result`, `/amcl_pose`, `navigation_controller/reach_goal`, `vocal_detect/wakeup`, `tts_node/tts_text`, `tts_node/play_finish`, `/controller/cmd_vel`, `servo_controller`, and services `~/transport_mode`, `~/transport_color` |
| Smart factory | [ros2_ws/src/large_models_examples/large_models_examples/function_calling/smart_factory/smart_factory.launch.py](/home/ubuntu/ros2_ws/src/large_models_examples/large_models_examples/function_calling/smart_factory/smart_factory.launch.py) | `smart_factory.py` uses `agent_process/tools`, `agent_process/result`, `/amcl_pose`, `navigation_controller/reach_goal`, `vocal_detect/wakeup`, `tts_node/tts_text`, `tts_node/play_finish`, `/controller/cmd_vel`, `line_following/min_distance_left`, `line_following/min_distance_right`, `servo_controller`, `~/result_image`, and the transport node publishes `~/transport_finished` with services such as `~/llm_enter`, `~/llm_exit`, `~/enable_transport`, `~/set_pick_position`, `~/set_place_position`, `~/record_position`, `~/go_home`, `~/go_home_pick`, `~/go_home_place`, `~/set_offset_z` |
| Road network tool | [ros2_ws/src/large_models_examples/large_models_examples/function_calling/road_network_llm/road_network_tool.launch.py](/home/ubuntu/ros2_ws/src/large_models_examples/large_models_examples/function_calling/road_network_llm/road_network_tool.launch.py) | `road_network_tool.py` uses `agent_process/tools`, `agent_process/result`, `/amcl_pose`, `/task_finish`, `/road_network_navigator/reach_final`, `/request_waypoint`, `vocal_detect/wakeup`, `tts_node/tts_text`, `tts_node/play_finish`, `/controller/cmd_vel`, `servo_controller`, `~/result_image`, and image subscriptions |

### Voice control stack

| Feature script | Launch file | Observed ROS interfaces |
|---|---|---|
| Mic init / ASR bootstrap | [ros2_ws/src/xf_mic_asr_offline/launch/mic_init.launch.py](/home/ubuntu/ros2_ws/src/xf_mic_asr_offline/launch/mic_init.launch.py) | Starts `awake_node.py`, `asr_node.py`, or `wonder_echo_pro_node.py` depending on mic type; `awake_node.py` publishes `~/angle` and `~/awake_flag`, services `~/set_mic_type`, `~/get_setting`, `~/set_wakeup_word`, `~/init_finish`; `asr_node.py` publishes `~/voice_words` and subscribes to `/awake_node/awake_flag` |
| Voice move | [ros2_ws/src/xf_mic_asr_offline/launch/voice_control_move.launch.py](/home/ubuntu/ros2_ws/src/xf_mic_asr_offline/launch/voice_control_move.launch.py) | `voice_control_move.py` publishes `/controller/cmd_vel` and `ros_robot_controller/set_buzzer`, subscribes to `/scan_raw`, `/asr_node/voice_words`, `/awake_node/angle`, and exposes `~/init_finish` |
| Voice navigation | [ros2_ws/src/xf_mic_asr_offline/launch/voice_control_navigation.launch.py](/home/ubuntu/ros2_ws/src/xf_mic_asr_offline/launch/voice_control_navigation.launch.py) | `voice_control_navigation.py` publishes movement and goal topics, subscribes to `/asr_node/voice_words` and `/awake_node/angle`, publishes buzzer control, and exposes `~/init_finish` |
| Voice navigation transport | [ros2_ws/src/xf_mic_asr_offline/launch/voice_control_navigation_transport.launch.py](/home/ubuntu/ros2_ws/src/xf_mic_asr_offline/launch/voice_control_navigation_transport.launch.py) | `voice_control_navigation_transport.py` subscribes to `/asr_node/voice_words`, publishes buzzer control, and exposes `~/init_finish` |
| Voice color track | [ros2_ws/src/xf_mic_asr_offline/launch/voice_control_color_track.launch.py](/home/ubuntu/ros2_ws/src/xf_mic_asr_offline/launch/voice_control_color_track.launch.py) | `voice_control_color_track.py` subscribes to `/asr_node/voice_words`, publishes buzzer control, and exposes `~/init_finish` |
| Voice color sorting | [ros2_ws/src/xf_mic_asr_offline/launch/voice_control_color_sorting.launch.py](/home/ubuntu/ros2_ws/src/xf_mic_asr_offline/launch/voice_control_color_sorting.launch.py) | `voice_control_color_sorting.py` subscribes to `/asr_node/voice_words`, publishes buzzer control, and exposes `~/init_finish` |
| Voice color detect | [ros2_ws/src/xf_mic_asr_offline/launch/voice_control_color_detect.launch.py](/home/ubuntu/ros2_ws/src/xf_mic_asr_offline/launch/voice_control_color_detect.launch.py) | `voice_control_color_detect.py` subscribes to `/asr_node/voice_words` and `/color_detect/color_info`, publishes buzzer control, and exposes `~/init_finish` |
| Voice garbage classification | [ros2_ws/src/xf_mic_asr_offline/launch/voice_control_garbage_classification.launch.py](/home/ubuntu/ros2_ws/src/xf_mic_asr_offline/launch/voice_control_garbage_classification.launch.py) | `voice_control_garbage_classification.py` subscribes to `/asr_node/voice_words`, publishes buzzer control, and exposes `~/init_finish` |
| Voice arm | [ros2_ws/src/xf_mic_asr_offline/launch/voice_control_arm.launch.py](/home/ubuntu/ros2_ws/src/xf_mic_asr_offline/launch/voice_control_arm.launch.py) | `voice_control_arm.py` subscribes to `/asr_node/voice_words`, publishes buzzer control and `servo_controller`, and exposes `~/init_finish` |

### Driver and peripheral support

| Launch file | Main node | Observed ROS interfaces |
|---|---|---|
| [ros2_ws/src/driver/controller/launch/controller.launch.py](/home/ubuntu/ros2_ws/src/driver/controller/launch/controller.launch.py) | controller stack | Includes odom, IMU, EKF, servo controller, and init pose; `odom_publisher_node.py` subscribes to `controller/cmd_vel` and `cmd_vel`, publishes `odom_raw`, `set_pose`, `ros_robot_controller/set_motor`, `ros_robot_controller/bus_servo/set_state`, and service `controller/load_calibrate_param` |
| [ros2_ws/src/driver/servo_controller/launch/servo_controller.launch.py](/home/ubuntu/ros2_ws/src/driver/servo_controller/launch/servo_controller.launch.py) | servo controller | `controller_manager.py` subscribes to `servo_controller` and `joint_controller`, publishes `~/joint_states` and `~/servo_states`, exposes `~/init_finish` |
| [ros2_ws/src/driver/ros_robot_controller/launch/ros_robot_controller.launch.py](/home/ubuntu/ros2_ws/src/driver/ros_robot_controller/launch/ros_robot_controller.launch.py) | hardware controller | Publishes `~/imu_raw`, `~/joy`, `~/sbus`, `~/button`, `~/battery`; subscribes to `~/set_led`, `~/set_buzzer`, `~/set_oled`, `~/set_motor`, `~/enable_reception`, `~/bus_servo/set_state`, `~/bus_servo/set_position`, `~/pwm_servo/set_state`; services `~/bus_servo/get_state`, `~/pwm_servo/get_state` |
| [ros2_ws/src/peripherals/launch/lidar.launch.py](/home/ubuntu/ros2_ws/src/peripherals/launch/lidar.launch.py) | lidar filter chain | Launches scan filtering nodes used by app lidar and line-following features |
| [ros2_ws/src/peripherals/launch/depth_camera.launch.py](/home/ubuntu/ros2_ws/src/peripherals/launch/depth_camera.launch.py) | camera stack | Launches camera pipeline used by vision apps; supports `/depth_cam/rgb/image_raw`, `/depth_cam/rgb/camera_info`, and depth topics |
| [ros2_ws/src/peripherals/launch/usb_cam.launch.py](/home/ubuntu/ros2_ws/src/peripherals/launch/usb_cam.launch.py) | USB camera | Exposes USB camera image topics used by Pro machines |

## Rebuild priority order

If you want to rebuild the custom app cleanly, the practical order is:

1. core transport/control: controller, servo controller, ros_robot_controller, lidar, camera
2. the app menu nodes in [ros2_ws/src/app/app/](/home/ubuntu/ros2_ws/src/app/app)
3. voice control in [ros2_ws/src/xf_mic_asr_offline/scripts/](/home/ubuntu/ros2_ws/src/xf_mic_asr_offline/scripts)
4. larger demo stacks in [ros2_ws/src/large_models_examples/large_models_examples/](/home/ubuntu/ros2_ws/src/large_models_examples/large_models_examples)
