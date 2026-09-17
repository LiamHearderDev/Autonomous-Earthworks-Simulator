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