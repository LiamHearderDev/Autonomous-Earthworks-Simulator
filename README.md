# Autonomous Earthworks Simulator

This repository is designed to simulate autonomous earthworks vehicles in a virtual environment using ROS2 Jazzy-Jalisco and Gazebo Harmonic. It provides models and controls for an excavator, allowing users to interact with these machines in a simulated setting. The excavator is based on the CAT 302 CR Mini Excavator model, and can be equipped with either a bucket or a Blast-Dog probe attachment. 

This README is split up into four sections:
1. Installation
2. Setup
3. Usage
4. GNSS data



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

# 4. GNSS data

GNSS starts automatically with the excavator simulator. It subscribes to `/odom` and publishes live position and orientation data, including while the excavator is stationary. Driving changes the position; turning changes the quaternion orientation and compass heading.

The geographic origin is Neubiberg: latitude `48.08028`, longitude `11.63806`, and altitude `553.0` metres. Position is derived from simulated wheel odometry relative to its starting point.

| Topic | ROS message type | Data |
| --- | --- | --- |
| `/fix` | `sensor_msgs/msg/NavSatFix` | Latitude and longitude in degrees, altitude in metres |
| `/gnss/pose` | `geometry_msgs/msg/PoseStamped` | Local position in metres and quaternion orientation in the odometry frame |
| `/gnss/heading` | `std_msgs/msg/Float64` | Compass heading in degrees: north = 0, east = 90, south = 180, west = 270 |

## Prepare a terminal

In each terminal used to view, record, or replay data, run these commands from the repository root:

```bash
source /opt/ros/jazzy/setup.bash
source excavator/install/setup.bash
```

## View live data

Start the simulator:

```bash
./earthworks cat-302-cr goose
```

In another prepared terminal, run one of these commands. Use separate terminals to view all three topics at once:

```bash
ros2 topic echo /fix
ros2 topic echo /gnss/pose
ros2 topic echo /gnss/heading
```

Press Ctrl+C to stop an echo command. Add `--once` to receive a single message.

## Save GNSS data

The GNSS node publishes live messages; it does not automatically save them to a file. While the simulator runs, start a ROS bag recording in another prepared terminal:

```bash
ros2 bag record -o gnss_recording /fix /gnss/pose /gnss/heading
```

Recording captures messages received after the recorder starts. Drive and turn using the teleop terminal to record changes in position and heading. Press Ctrl+C in the recording terminal to stop and finish writing the bag before closing the simulator.

The command creates `gnss_recording/` inside the directory where it was run. The folder contains `metadata.yaml` and the recorded message data, typically in an `.mcap` file. Keep the entire folder to inspect, replay, or share the saved GNSS data offline.

The output folder must not already exist. If `gnss_recording/` exists, choose a new name, such as `gnss_recording_2`, and use that name in the inspection and playback commands below.

## Inspect and replay saved data

With the simulator stopped, inspect the recording from the directory containing its folder:

```bash
ros2 bag info gnss_recording
```

This shows the recording duration, topics, message types, and message counts. No running Gazebo instance is required.

In another prepared terminal, start listening before playback:

```bash
ros2 topic echo /fix
```

Then replay the bag in the first terminal:

```bash
ros2 bag play gnss_recording
```

Playback republishes the saved messages on `/fix`, `/gnss/pose`, and `/gnss/heading`. Use the corresponding echo commands to view the saved pose and heading too. Playback ends when the recording finishes; use `ros2 bag play --loop gnss_recording` for repeated playback and Ctrl+C to stop it.

## Export saved GNSS data to readable text

The `.mcap` or `.db3` data inside a ROS bag is binary and cannot be read in a text editor. Use `gnss_export` to create a readable `.txt` copy of the saved latitude, longitude, altitude, local position, quaternion orientation, and compass heading. It reads the bag directly, so no simulator, playback, or echo terminals are needed.

After installing this feature, build the excavator package once from the repository root:

```bash
source /opt/ros/jazzy/setup.bash
cd excavator
colcon build --symlink-install --packages-select excavator
cd ..
source excavator/install/setup.bash
```

Finish recording with Ctrl+C, then export the saved bag from a prepared terminal:

```bash
ros2 run excavator gnss_export gnss_recording
```

This creates `gnss_recording.txt` next to the `gnss_recording/` folder. Open it in any text editor to view all recorded GNSS messages, their timestamps, units, and message counts. The original bag stays unchanged.

To choose a different output filename:

```bash
ros2 run excavator gnss_export gnss_recording -o gnss_data.txt
```

Relative output paths are saved in the directory where you run the command. You can also provide absolute paths to the bag and output file. The output directory must already exist. Existing files are never overwritten; choose another filename with `-o` for a new export.

The exporter supports MCAP and SQLite3 ROS bag directories. It exports the available `/fix`, `/gnss/pose`, and `/gnss/heading` messages, ignores unrelated topics, and reports the count for each GNSS topic. A bag containing only `/fix` can still be exported; missing GNSS topics have a count of zero. A bag with no recorded GNSS messages produces an error.

ROS bags preserve the original messages for replay and future exports. The text export is a readable copy rather than a CSV spreadsheet. See the [ROS bag documentation](https://github.com/ros2/rosbag2) for more recording and playback options.
