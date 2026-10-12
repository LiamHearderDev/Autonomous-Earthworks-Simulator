#!/usr/bin/env python3

# This is where the code for the deformable soil terrain system will be placed.

import os
import rclpy
from rclpy.node import Node as RosNode

from gz.transport13 import Node as GzNode
from gz.msgs10.pose_pb2 import Pose
from gz.msgs10.pose_v_pb2 import Pose_V
import numpy as np


class SoilParams:
    """ Contains all of the data required by the SoilFieldManager. """

    # TODO: Make these adjustable via ROS params, perhaps
    grid_cells: int = 25            # cells per side
    cell_size: float = 1.0          # metres
    origin: tuple = (0.0, 0.0)      # world (x,y) of cell [0,0]
    base_height: float = 0.0        # initial terrain height
    cut_depth: float = 0.01         # metres removed per pose update while digging
    stiffness: float = 20000.0      # N/m   (start soft)
    damping: float = 4000.0         # N*s/m
    max_force: float = 50000.0      # N, cap so the arm stalls not explodes
    bucket_location: tuple = (0.0, 0.0, 0.0)    # x, y, z
    bucket_up_axis: tuple = (0.0, 0.0, 1.0)     # axis pointing out of the bucket
    dump_threshold: float = 0.2     # Dump payload when world-up-z falls below this value
    dump_rate: float = 0.02         # m^3 per second while dumping

### SoilParams ###



class HeightGrid:
    """ A NumPy heightfield. Handles bilinear lookup, cutting a cell 
    down (which returns removed volumed), and raisidng a cell up. """

    def __init__(self, params: SoilParams):
        self.params = params

        cell_count = params.grid_cells
        self.grid = np.full(
            shape=(cell_count,cell_count),
            fill_value=params.base_height,
            dtype=np.float32,
            order='C'
            )
        self.should_update_visuals = False

    def to_local_coords(self, x, y) -> tuple[float, float]:
        """ Converts a world position (x,y) to a local grid cell. Does not
        check if the result is out of bounds. """
        cell_x = (x - self.params.origin[0]) / self.params.cell_size
        cell_y = (y - self.params.origin[1]) / self.params.cell_size
        return cell_x, cell_y

    def _nearest_cell_indices(self, x, y) -> tuple[int, int] | None:
        cell_x, cell_y = self.to_local_coords(x, y)
        nearest_x, nearest_y = int(round(cell_x)), int(round(cell_y))
        cell_count = self.params.grid_cells
        if 0 <= nearest_x < cell_count and 0 <= nearest_y < cell_count:
            return nearest_x, nearest_y
        return None

    def is_in_bounds(self, x, y) -> bool:
        """ Checks if, given an (x,y) world coordinate, a world location is
        within the bounds of the grid. """
        return self._nearest_cell_indices(x, y) is not None

    def get_height(self, x, y) -> float | None:
        """Return the nearest cell height, or None when outside the grid."""
        indices = self._nearest_cell_indices(x, y)
        if indices is None:
            return None
        return float(self.grid[indices[0], indices[1]])

    def lower_height(self, x, y, new_height) -> float:
        """ Lowers the height of a cell at world location (x,y) to a new
        height value. Returns the removed volume in m^3 """

        indices = self._nearest_cell_indices(x, y)
        if indices is None:
            return 0.0

        old_height = float(self.grid[indices[0], indices[1]])
        if new_height >= old_height:
            return 0.0

        self.grid[indices[0], indices[1]] = new_height
        self.should_update_visuals = True
        return (old_height - new_height) * self.params.cell_size ** 2


    def deposit(self, x, y, volume) -> None:
        """ Adds volume to a specific (x,y) location. """
        indices = self._nearest_cell_indices(x, y)
        if indices is None or volume <= 0.0:
            return

        self.grid[indices[0], indices[1]] += volume / self.params.cell_size ** 2
        self.should_update_visuals = True

    # TODO: maybe add a relaxation function?

### HeightGrid ###



class SoilModel:
    """ Designed to handle physics updates, and visual model changes. """

    def __init__(self, params: SoilParams, grid: HeightGrid):
        self.params = params
        self.grid = grid
        self.bucket_payload = 0.0   # measured in m^3
        self.bucket_location = params.bucket_location
        self.bucket_up_axis = params.bucket_up_axis

    def step(self) -> float:
        """ TODO: Should return (force, torque) in world space. """
        return 0.0, 0.0

    def try_dump(self, position) -> None:
        """ TODO: Should check if the world's up-axis (relative to model) is 
        below the dump threshold. If it is, dump out the contents. """

        # Check bounds
        return
### SoilModel ###          



class SoilNode(RosNode):
    """Tracks the bucket and removes soil from the nearest grid cell."""

    def __init__(self):
        super().__init__('soil_node')
        self.params = SoilParams()
        self.grid = HeightGrid(self.params)
        self.model = SoilModel(self.params, self.grid)

        self.declare_parameter("robot_name", "excavator")
        self.declare_parameter("world_path", "worlds/aarp_goose_demo_v2.sdf")
        self.declare_parameter("cut_depth", self.params.cut_depth)

        robot_name: str = self.get_parameter("robot_name").value
        world_path: str = self.get_parameter("world_path").value
        self.params.cut_depth = float(self.get_parameter("cut_depth").value)
        if self.params.cut_depth <= 0.0:
            raise ValueError("The cut_depth parameter must be greater than zero")

        world_name = os.path.splitext(os.path.basename(world_path))[0]
        pose_topic = f"/world/{world_name}/pose/info"

        self.robot_name = robot_name
        self.bucket_pose: Pose | None = None
        self.soil_field_pose: Pose | None = None
        self.gz_node = GzNode()
        self.pose_subscription = self.gz_node.subscribe(
            Pose_V,
            pose_topic,
            self.pose_callback,
        )
        if not self.pose_subscription:
            raise RuntimeError(f"Failed to subscribe to Gazebo topic {pose_topic}")

        self.get_logger().info(
            f"Listening for {robot_name!r} bucket and 'soil_field' "
            f"poses on {pose_topic}"
        )

    def pose_callback(self, msg: Pose_V) -> None:
        """Track bucket height and cut the nearest cell when it penetrates soil."""
        for model_pose in msg.pose:
            entity_parts = model_pose.name.split("::")
            if (
                entity_parts[-1] == "bucket"
                and self.robot_name in entity_parts[:-1]
            ):
                self.bucket_pose = Pose()
                self.bucket_pose.CopyFrom(model_pose)
            elif entity_parts[-1] == "soil_field":
                self.soil_field_pose = Pose()
                self.soil_field_pose.CopyFrom(model_pose)

        if self.bucket_pose is None:
            return

        bucket_position = self.bucket_pose.position
        cell_height = self.grid.get_height(bucket_position.x, bucket_position.y)
        if cell_height is None:
            return

        soil_base_height = (
            self.soil_field_pose.position.z
            if self.soil_field_pose is not None
            else 0.0
        )
        soil_surface_height = soil_base_height + cell_height
        if bucket_position.z < soil_surface_height:
            self.grid.lower_height(
                bucket_position.x,
                bucket_position.y,
                cell_height - self.params.cut_depth,
            )



### SoilNode ###


def main(args=None):
    rclpy.init(args=args)

    soil_node = SoilNode()

    try:
        rclpy.spin(soil_node)
    finally:
        soil_node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()