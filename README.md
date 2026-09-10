# Autonomous Earthworks Simulator — Bulldozer Movement

ROS 2 Jazzy and Gazebo Harmonic bulldozer starting point, adapted from the
Desktop `Autonomous-Earthworks-Simulator-Excavator-Movement` project. It uses
the same nested Python package layout, launch flow, empty world, chassis,
four wheels, and differential-drive plugin.

The excavator arm, arm joint controller, arm keyboard node, and excavator
mesh are excluded. The current machine is a driveable four-wheel placeholder.
Bulldozer tracks, blade geometry, blade controls, and their dependencies will
be added later.

## Project layout

```text
Autonomous-Earthworks-Simulator/
├── CMakeLists.txt                 # Future C++ physics plugin scaffold
├── README.md
├── bulldozer/                     # ROS 2 package (ament_python)
│   ├── bulldozer/
│   │   └── __init__.py            # Future bulldozer Python nodes go here
│   ├── config/
│   │   └── bulldozer_bridge.yaml
│   ├── launch/
│   │   └── robot.launch.py
│   ├── resource/
│   │   └── bulldozer              # ROS package discovery marker
│   ├── urdf/
│   │   └── bulldozer.urdf.xacro
│   ├── worlds/
│   │   └── bulldozer_empty.sdf
│   ├── package.xml               # Runtime dependencies
│   ├── setup.cfg
│   └── setup.py                  # Installs the package and simulation files
├── src/
│   └── plugin.cc                 # Reference's future physics plugin notes
├── static/
│   ├── README.txt
│   └── models/bulldozer/source/
│       └── README.txt            # Location for future bulldozer mesh assets
└── worlds/
    ├── ae_bulldozer.sdf          # Ground and sunlight
    └── ae_test.sdf               # Reference's ground, cone, and box scene
```

`CMakeLists.txt` and `src/plugin.cc` are placeholders from the reference;
they do not build a physics plugin yet. The ROS package is built by
`bulldozer/setup.py`. Build outputs (`build/`, `install/`, and `log/`) are
ignored by Git.

## Build and run

From the repository root:

```bash
source /opt/ros/jazzy/setup.bash
colcon build --base-paths bulldozer --symlink-install
source install/setup.bash
ros2 launch bulldozer robot.launch.py
```

Use `--base-paths bulldozer` to select the ROS package separately from the
root CMake scaffold. After sourcing the installation, the default launch
works from any directory because the world is installed with the package.

Gazebo opens with the same Teleop panel as the reference. Use it to drive
the base on `cmd_vel`. For optional terminal keyboard control, install
`ros-jazzy-teleop-twist-keyboard`, then run in a second terminal:

```bash
source /opt/ros/jazzy/setup.bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard
```

To spawn the same bulldozer in the obstacle world, run from the repository root:

```bash
ros2 launch bulldozer robot.launch.py world:="$PWD/worlds/ae_test.sdf"
```

To run the simulation without opening a window:

```bash
ros2 launch bulldozer robot.launch.py gui:=false
```

The root worlds can also be opened directly with `gz sim worlds/ae_test.sdf`
after sourcing ROS. That previews the terrain and obstacles; the ROS launch
file is responsible for spawning the vehicle.

## How the code works

1. `robot.launch.py` locates the installed package and expands the xacro.
2. `robot_state_publisher` publishes the robot description and link transforms.
3. Gazebo loads `bulldozer_empty.sdf`, and `ros_gz_sim create` spawns the robot.
4. The URDF's `DiffDrive` plugin drives both wheels on each side. Its
   `JointStatePublisher` reports wheel positions for the transform tree.
5. `bulldozer_bridge.yaml` connects ROS commands and Gazebo feedback:

| ROS topic | Gazebo topic | Direction / purpose |
| --- | --- | --- |
| `/cmd_vel` | `/cmd_vel` | ROS → Gazebo drive command |
| `/odom` | `/odom` | Gazebo → ROS odometry |
| `/tf` | `/model/bulldozer/tf` | Gazebo → ROS `odom` to `base_link` transform |
| `/joint_states` | `/joint_states` | Gazebo → ROS wheel joint states |
| `/clock` | `/clock` | Gazebo → ROS simulation time |

The inertia-free `base_link` is fixed to the physical `chassis`. The chassis
and wheel dimensions, masses, friction, and drive settings retain the
reference values; they are placeholders for later bulldozer modelling.

## Base software dependencies

The movement scaffold uses the reference's ROS/Gazebo stack. On a machine
with ROS 2 Jazzy configured, the main packages can be installed with:

```bash
sudo apt install -y \
    python3-colcon-common-extensions \
    python3-setuptools \
    ros-jazzy-ros-gz-sim \
    ros-jazzy-ros-gz-bridge \
    ros-jazzy-robot-state-publisher \
    ros-jazzy-xacro
```

`bulldozer/package.xml` lists the runtime dependencies. There is no arm
dependency or blade-control executable in this version.
