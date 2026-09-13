# Autonomous-Earthworks-Simulator

This is a Gazebo simulation of autonomous earthworks vehicles. The simulation is designed to be used with ROS2, but it can also be run without ROS2, just with Gazebo. 

The current stage of the simulation includes a test world with an excavator and basic terrain.

# How to launch the excavator world (without ROS2):

### 1. Configure and build the project:
```bash
cmake -S . -B build && cmake --build build
```

### 2. Navigate to the project directory.
```bash
cd /path/to/Autonomous-Earthworks-Simulator
```

### 3. Set your Gazebo simulation resource path to the working directory:
```bash
export GZ_SIM_RESOURCE_PATH=${GZ_SIM_RESOURCE_PATH}:$(pwd)
```

### 4. Open Gazebo and load the test world:
```bash
gz sim worlds/ae_test.sdf
```
You should now be able to see the excavator in the Gazebo simulation environment. If you would like to be able to control the excavator with ROS2, please follow the instructions below.

# How to launch the excavator world (with ROS2):

### 1. Install all required packages and dependencies for ros2 <-> gazebo integration:
```bash
sudo apt install -y \
    ros-jazzy-ros-gz \
    ros-jazzy-ros-gz-bridge \
    ros-jazzy-joint-state-publisher \
    ros-jazzy-xacro \
    ros-jazzy-teleop-twist-keyboard
```
Note: `ros-jazzy-teleop-twist-keyboard` is optional and only needed if you want to control the excavator with keyboard input in the terminal.

### 2. Configure and build the project:
```bash
cmake -S . -B build && cmake --build build
```

### 3. Source your ROS2 workspace:
```bash
source /opt/ros/jazzy/setup.bash
```

### 4. Navigate to the project root directory.
```bash
cd /path/to/Autonomous-Earthworks-Simulator
```

### 5. Set your Gazebo simulation resource path to the working directory:
```bash
export GZ_SIM_RESOURCE_PATH=${GZ_SIM_RESOURCE_PATH}:$(pwd)
```

### 6. Navigate to the excavator package directory:
```bash
cd excavator
```

### 7. Build the ROS2 package:
```bash
colcon build --symlink-install
```

### 8. Source the ROS2 workspace:
```bash
source install/setup.bash
```

### 9. Launch the Gazebo simulation with ROS2:
```bash
ros2 launch excavator robot.launch.py
```

### 10. In a separate terminal, launch the arm_teleop control application:
First, execute step 8 in the new terminal, then:
```bash
cd path/to/Autonomous-Earthworks-Simulator/excavator

source install/setup.bash

ros2 run excavator arm_teleop
```