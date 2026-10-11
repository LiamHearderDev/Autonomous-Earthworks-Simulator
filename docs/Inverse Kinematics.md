# Inverse Kinematics

To implement inverse kinematics, MoveIt2 has been decided as the platform

## Installation

```
sudo apt update 
sudo apt install ros-jazzy-moveit
sudo apt install ros-jazzy-moveit-py
```

## Setup

Setup has been done using the setup assistant first to create the necessary files, using the group of steps under: https://moveit.picknik.ai/main/doc/examples/examples.html#integration-with-a-new-robot

Here is the setup assistant guide: https://moveit.picknik.ai/main/doc/examples/setup_assistant/setup_assistant_tutorial.html

You can run it with:  
 ```ros2 launch moveit_setup_assistant setup_assistant.launch.py```

Generating the files at the end of the assistant will create a dedicated python package, which already works seamlessly with our project structure. This may not work if setting the directory as excavator due to overwriting files, though the necessary files can be moved to their respective areas

**New files added**
```
excavator
|
|- .setup_assistant
|
|- config
|    |- excavator.ros2_control.xacro
|    |- excavator.srdf
|    |- excavator.urdf.xacro
|    |- initial_positions.yaml
|    |- joint_limits.yaml
|    |- kinematics.yaml
|    |- moveit.rviz
|    |- pilz_cartesian_limits.yaml
```

Note: There are repeating files like for ros2 control and urdf that can probably be removed and pointed to the exisiting files, though srdf is new and important

Changes are made to:  
- robot.launch.py (adding a new ndoe to the launch description)
- excavator_teleop.py (executes the planning code and sends messages back to gazebo)

Some of these files may not be needed, this is a WIP