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
    ros-jazzy-rviz2 \
    ros-jazzy-cv-bridge
```

From the repository root, navigate to the `excavator` package directory:
```bash
cd excavator
```

Source the ROS 2 environment:
```bash
source /opt/ros/jazzy/setup.bash
```

Build the excavator from the repository root:
```bash
colcon --log-base /dev/null build --symlink-install
source install/setup.bash
```

Launch the excavator robot:
```bash
ros2 launch excavator robot.launch.py
```
---

In another terminal, start its keyboard controller:

```bash
cd excavator
source /opt/ros/jazzy/setup.bash
source install/setup.bash
ros2 run excavator excavator_teleop
```

Use numpad `8`/`2` for the arm, numpad `4`/`6` for chassis rotation, `5` to
stop, and `Q` to quit.