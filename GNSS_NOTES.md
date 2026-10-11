# GNSS Implementation Notes

## Short explanation for the group

Our Gazebo environment uses local coordinates measured in metres. The world has
an `x`, `y`, and `z` position, but it does not currently have a real latitude or
longitude.

To simulate GNSS, we can assign a real geographic coordinate to the world
origin `(0, 0, 0)`. We can then convert the excavator's position relative to
that origin into latitude, longitude, and altitude.

The GOOSE dataset is a German outdoor and off-road dataset. As a representative
reference point, we could place the simulation origin near the University of
the Bundeswehr Munich in Neubiberg, Germany:

```text
Gazebo world origin: x = 0, y = 0, z = 0
Latitude:            48.08028 degrees
Longitude:           11.63806 degrees
Altitude:             approximately 553 metres
```

This would be an assigned simulation reference. It would not mean that our
synthetic heightmap is an exact recreation of that location. If we use an
actual GOOSE recording, we should first check its metadata and localisation
topics for the real origin used by that recording.

## Coordinate convention

We can define the simulator axes as:

```text
Gazebo x = metres east
Gazebo y = metres north
Gazebo z = metres above the selected origin
```

For example, a world position of:

```text
x = 10, y = 20, z = 2
```

means that the excavator is 10 metres east, 20 metres north, and 2 metres above
the selected geographic origin.

## Odometry and GNSS

Odometry and GNSS both describe position, but they are different.

Odometry (`/odom`) provides:

- local `x`, `y`, and `z` position;
- orientation;
- linear and angular velocity;
- a timestamp.

GNSS (`/fix`) provides:

- latitude;
- longitude;
- altitude;
- estimated accuracy;
- a timestamp.

Odometry is normally smooth and updates quickly, but on a real machine it can
drift over time. GNSS supplies a global geographic reference that can be used
to correct that drift.

In our simulator, a GNSS conversion node could read the excavator's current
world position, convert it relative to the selected German origin, and publish
the result as a ROS 2 `sensor_msgs/msg/NavSatFix` message on `/fix`.

## Joint states

The `/joint_states` topic is separate from GNSS. It reports the state of the
robot's movable joints, such as:

- the upper-arm angle;
- the lower-arm angle;
- the chassis rotation;
- the BLASTDOG probe position;
- joint velocities;
- the measurement timestamp.

The timestamps allow us to determine the machine's GNSS position and joint
configuration at the same point in time.

For example, we could determine that at a particular timestamp the excavator
was at a certain latitude and longitude while its arm and BLASTDOG probe were
in particular positions.

## Teleoperation

The teleoperation node does not create GNSS data. It sends commands that move
the machine and its joints:

```text
Keyboard input
      -> teleoperation node
      -> ROS 2 controllers
      -> excavator moves
      -> odometry, GNSS, TF, and joint states update
```

## Important ROS 2 topics

| Topic | Purpose |
| --- | --- |
| `/odom` | Local position, orientation, and velocity |
| `/fix` | GNSS latitude, longitude, and altitude |
| `/joint_states` | Positions and velocities of robot joints |
| `/tf` | Changing relationships between coordinate frames |
| `/tf_static` | Fixed relationships, such as sensor mounting positions |
| `/lidar/points` | LiDAR point cloud when the LiDAR is implemented |

## Viewing and saving the output

The topics can be inspected from a ROS 2 terminal. For example:

```bash
ros2 topic echo /odom
ros2 topic echo /fix
ros2 topic echo /joint_states
```

They can be recorded together using ROS bag:

```bash
ros2 bag record /fix /odom /joint_states /tf /tf_static
```

After LiDAR is implemented, it can be included in the same recording:

```bash
ros2 bag record /fix /odom /joint_states /tf /tf_static /lidar/points
```

Because these messages contain timestamps, the recorded sensor and robot data
can be compared later.

## Overall design

```text
Keyboard
   |
   v
Teleoperation node
   |
   v
Robot controllers
   |
   v
Gazebo excavator
   |-- local pose and movement ------------> /odom
   |-- joint positions --------------------> /joint_states
   |-- coordinate-frame relationships -----> /tf
   |-- world position -> GNSS conversion --> /fix
   `-- LiDAR sensor ------------------------> /lidar/points

All required topics ------------------------> ROS bag recording
```

## Suggested implementation order

1. Launch the excavator and confirm that `/odom` publishes changing data.
2. Confirm that `/joint_states`, `/tf`, and `/tf_static` are available.
3. Decide whether to use an actual GOOSE sequence origin or the representative
   Neubiberg origin.
4. Clearly document the axis convention: `x` east, `y` north, and `z` up.
5. Obtain the excavator's world position at each timestamp.
6. Convert the local position into latitude, longitude, and altitude.
7. Publish the result on `/fix` using `NavSatFix`.
8. View `/odom`, `/fix`, and the robot frames in ROS tools or RViz.
9. Record the required topics using ROS bag.
10. Add LiDAR and include `/lidar/points` when that requirement is implemented.

## Points to confirm before implementation

- Does the requirement specifically require GNSS latitude and longitude, or is
  local position and orientation from `/odom` sufficient?
- Must the origin match a particular GOOSE recording?
- Should GNSS be perfect, or should simulated noise and reduced accuracy be
  included?
- Is ROS bag the agreed documented output method?
- Does the GNSS position represent the excavator base, a GNSS antenna link, or
  another point on the machine?

## Very short presentation version

> Our Gazebo world currently uses local metre-based coordinates and has no real
> geographic location. We can assign the world origin a known coordinate in
> Germany and treat world `x` as east, `y` as north, and `z` as height. A ROS 2
> conversion node can then convert the excavator's world position into latitude,
> longitude, and altitude and publish it on `/fix`. Odometry remains available
> on `/odom`, while `/joint_states` reports the arm and BLASTDOG probe positions.
> All of these topics share timestamps and can be recorded together in a ROS bag
> for later analysis.
