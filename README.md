# Autonomous Earthworks Simulator

This repository is designed to simulate autonomous earthworks vehicles in a virtual environment using ROS2 Jazzy-Jalisco and Gazebo Harmonic. It provides models and controls for an excavator, allowing users to interact with these machines in a simulated setting. The excavator is based on the CAT 302 CR Mini Excavator model, and can be equipped with either a bucket or a Blast-Dog probe attachment. 

This README is split up into three sections:
1. Installation
2. Setup
3. Usage



# 1. Installation
Currently, the only supported Operating System is Linux, Ubuntu-24.04. Steps for each OS can be found below.

## Ubuntu 24.04
By far the simplest way to run the project is to use the provided Dockerfile. This will set up a containerised environment with all necessary dependencies, including ROS2 Jazzy-Jalisco and Gazebo Harmonic.

To obtain the Docker image with all required dependencies, run the following command:
```bash
sudo docker pull liamhearderdev/earthworks:latest
```

Then to run the container, first navigate to the project root:
```bash
cd /path/to/Autonomous-Earthworks-Simulator
```

And execute the following script to run the Docker image:
```bash
sudo bash scripts/docker_run.bash
```

Progress to the Setup section below to run the simulator.

## Windows 10/11
To run the project on Windows, use Windows Subsystem for Linux (WSL) with Ubuntu-24.04. Then follow the above steps.

## MacOS
MacOS is currently unsupported. To run the project on MacOS, dual-booting or using a VM with Ubuntu-24.04 is the best option, but performance and stability cannot be guaranteed.


# 2. Setup
To begin the setup process, run the build script:
```bash
source scripts/build.bash
```

# 3. Usage
Now that the project has been properly setup, you are all set to go! Run the simulator from the repository root and pass through the options you'd like:
```bash
./earthworks <machine> <environment>
```

Machines are `cat-302-cr` and `blast-dog`; environments are `goose` and `empty`. The command loads the ROS 2 environment and launches Gazebo with the chosen world. Run `./earthworks --help` to display the available values.

As soon as the project opens, you'll notice a new terminal window opening. It's from this window that you'll be able to control the earthworks vehicle.