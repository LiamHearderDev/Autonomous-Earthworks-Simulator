# Autonomous Earthworks Simulator

This repository contains ROS 2 and Gazebo simulations for a bulldozer and an
excavator.

## Packages

- `bulldozer/` contains the wheeled bulldozer, movable blade, sand world, and
  keyboard controller.
- `excavator/` contains the excavator, arm controls, and ROS 2 controllers.

## Bulldozer

Build and launch the bulldozer from the repository root:

```bash
cd bulldozer
source /opt/ros/jazzy/setup.bash
colcon --log-base /dev/null build --symlink-install
source install/setup.bash
ros2 launch bulldozer robot.launch.py
```

In another terminal, start its keyboard controller:

```bash
cd bulldozer
source /opt/ros/jazzy/setup.bash
source install/setup.bash
ros2 run bulldozer keyboard_teleop
```

Use `W`/`S` to drive, `A`/`D` to turn, Space or `X` to stop, `R`/`F` to
raise or lower the blade, and `Q` to quit.

## Excavator

Install the excavator controller dependencies if needed:

```bash
sudo apt install -y \
    ros-jazzy-ros-gz \
    ros-jazzy-ros-gz-bridge \
    ros-jazzy-joint-state-publisher \
    ros-jazzy-xacro \
    ros-jazzy-teleop-twist-keyboard \
    ros-jazzy-ros2launch \
    ros-jazzy-ros2run \
    ros-jazzy-gz-ros2-control \
    ros-jazzy-ros2-controllers \
    ros-jazzy-rviz2
```

Build and launch the excavator from the repository root:

```bash
cd excavator
source /opt/ros/jazzy/setup.bash
colcon --log-base /dev/null build --symlink-install
source install/setup.bash
ros2 launch excavator robot.launch.py
```

In another terminal, start its keyboard controller:

```bash
cd excavator
source /opt/ros/jazzy/setup.bash
source install/setup.bash
ros2 run excavator excavator_teleop
```

Use numpad `8`/`2` for the arm, numpad `4`/`6` for chassis rotation, `5` to
stop, and `Q` to quit.
