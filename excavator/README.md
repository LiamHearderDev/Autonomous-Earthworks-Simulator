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

Use numpad `8`/`2` and `7`/`1` for the arm, numpad `4`/`6` for chassis
rotation, and `5` to stop. On the BLASTDOG variant, numpad `9` raises the
probe and numpad `3` lowers it. Press `Q` to quit.
