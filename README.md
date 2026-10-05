# Autonomous Earthworks Simulator

This repository contains ROS 2 and Gazebo simulations for a bulldozer and an
excavator.

Run the simulator from the repository root by passing the machine and
environment names:

```bash
./earthworks cat-302-cr goose
```

Machines are `cat-302-cr` and `blast-dog`; environments are `goose` and `empty`.
The command loads the ROS 2 environment and launches Gazebo with the chosen
world. Until its own simulation model is added, `blast-dog` temporarily uses the
CAT excavator model. Run `./earthworks --help` to display the available values.

## Packages

- `bulldozer/` contains the wheeled bulldozer, movable blade, sand world, and
  keyboard controller.
- `excavator/` contains the excavator, arm controls, and ROS 2 controllers.

## Compilation Steps

### 1. Install all dependencies:
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

### 2. Navigate to the project directory.
```bash
cd /path/to/Autonomous-Earthworks-Simulator
```

### 3. Configure and build the project:
```bash
cmake -S . -B build && cmake --build build
```

### 4. Set your Gazebo simulation resource path to the working directory:
```bash
export GZ_SIM_RESOURCE_PATH=${GZ_SIM_RESOURCE_PATH}:$(pwd)
```

### 5. Build both packages
```bash
cd bulldozer
colcon build --symlink-install
cd ..
```
and
```bash
cd excavator
colcon build --symlink-install
cd ..
```

### 6. Navigate to the package you wish to run, and follow the steps below
```bash
cd excavator
```
or
```bash
cd bulldozer
```


## Excavator

Build and launch the excavator from the repository root:

1. Load the ROS2 environment for Jazzy Jalisco. This ensures that ROS2 commands will work as needed.
```bash
source /opt/ros/jazzy/setup.bash
```

2. Build the workspace using Colcon. This compiles all packages in the workspace and installs them to `install/`.
```bash
colcon --log-base /dev/null build --symlink-install
```

3. Load the environment workspace built by Colcon.
```bash
source install/setup.bash
```

4. Launch the excavator robot through ROS2.
```bash
ros2 launch excavator robot.launch.py
```

---

In another terminal, start its keyboard controller:

```bash
cd /path/to/Autonomous-Earthworks-Simulator/excavator
source /opt/ros/jazzy/setup.bash
source install/setup.bash
ros2 run excavator excavator_teleop
```

Use numpad `8`/`2` for the arm, numpad `4`/`6` for chassis rotation, `5` to
stop, and `Q` to quit.


## Bulldozer

Build and launch the bulldozer from the repository root:



1. Load the ROS2 environment for Jazzy Jalisco. This ensures that ROS2 commands will work as needed.
```bash
source /opt/ros/jazzy/setup.bash
```

2. Build the workspace using Colcon. This compiles all packages in the workspace and installs them to `install/`.
```bash
colcon --log-base /dev/null build --symlink-install
```

3. Load the environment workspace built by Colcon.
```bash
source install/setup.bash
```

4. Launch the bulldozer robot through ROS2.
```bash
ros2 launch bulldozer robot.launch.py
```

---

In another terminal, start its keyboard controller:

```bash
cd /path/to/Autonomous-Earthworks-Simulator/bulldozer
source /opt/ros/jazzy/setup.bash
source install/setup.bash
ros2 run bulldozer keyboard_teleop
```

Use `W`/`S` to drive, `A`/`D` to turn, Space or `X` to stop, `R`/`F` to
raise or lower the blade, and `Q` to quit.
