#!/usr/bin/env python3

# This is where the code for the deformable soil terrain system will be placed.

import tempfile
import threading
import xml.etree.ElementTree as ET
from pathlib import Path
from xml.sax.saxutils import escape

from ament_index_python.packages import get_package_share_directory
import rclpy
from rclpy.node import Node as RosNode

from gz.transport13 import Node as GzNode
from gz.msgs10.boolean_pb2 import Boolean
from gz.msgs10.entity_factory_pb2 import EntityFactory
from gz.msgs10.entity_pb2 import Entity
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
        self.should_update_visuals = True

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
    """Cuts soil under the bucket and refreshes its Gazebo terrain mesh."""

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

        world_file = Path(world_path).expanduser()
        if not world_file.is_file():
            world_file = Path(get_package_share_directory("excavator")) / world_path
        if not world_file.is_file():
            raise FileNotFoundError(f"Could not find Gazebo world file: {world_path}")

        world_element = ET.parse(world_file).getroot().find("world")
        if world_element is None or not world_element.get("name"):
            raise ValueError(f"World file has no named <world>: {world_file}")
        world_name = world_element.get("name")
        pose_topic = f"/world/{world_name}/pose/info"
        self.gz_create_service = f"/world/{world_name}/create"
        self.gz_remove_service = f"/world/{world_name}/remove"

        self.robot_name = robot_name
        self.bucket_pose: Pose | None = None
        self._grid_lock = threading.Lock()
        self._mesh_directory = Path(tempfile.mkdtemp(prefix="soil_terrain_"))
        self._mesh_revision = 0
        self._terrain_visuals: dict[str, Path] = {}
        self._current_visual_name: str | None = None
        self.gz_node = GzNode()
        self.pose_subscription = self.gz_node.subscribe(
            Pose_V,
            pose_topic,
            self.pose_callback,
        )
        if not self.pose_subscription:
            raise RuntimeError(f"Failed to subscribe to Gazebo topic {pose_topic}")

        self.get_logger().info(
            f"Listening for {robot_name!r} bucket poses on {pose_topic}; "
            f"terrain meshes will be spawned through {self.gz_create_service}"
        )
        self._visual_timer = self.create_timer(0.2, self._update_terrain_visual)

    def pose_callback(self, msg: Pose_V) -> None:
        """Cut the nearest cell when the bucket link penetrates the grid."""
        with self._grid_lock:
            for model_pose in msg.pose:
                entity_parts = model_pose.name.split("::")
                if (
                    entity_parts[-1] == "bucket"
                    and self.robot_name in entity_parts[:-1]
                ):
                    self.bucket_pose = Pose()
                    self.bucket_pose.CopyFrom(model_pose)

            if self.bucket_pose is None:
                return

            bucket_position = self.bucket_pose.position
            cell_height = self.grid.get_height(
                bucket_position.x,
                bucket_position.y,
            )
            if cell_height is not None and bucket_position.z < cell_height:
                self.grid.lower_height(
                    bucket_position.x,
                    bucket_position.y,
                    cell_height - self.params.cut_depth,
                )

    def _write_terrain_mesh(self, heights: np.ndarray, revision: int) -> Path:
        """Write the height grid as a closed, triangulated Wavefront OBJ mesh."""
        cell_count = self.params.grid_cells
        mesh_count = cell_count + 2
        mesh_path = self._mesh_directory / f"terrain_{revision}.obj"
        bottom_height = min(float(np.min(heights)), self.params.base_height) - max(
            self.params.cell_size,
            0.1,
        )

        def top_index(x: int, y: int) -> int:
            return x * mesh_count + y + 1

        def bottom_index(x: int, y: int) -> int:
            return mesh_count * mesh_count + top_index(x, y)

        def sample_index(mesh_index: int) -> int:
            return min(max(mesh_index - 1, 0), cell_count - 1)

        def vertex_coordinate(mesh_index: int) -> float:
            if mesh_index == 0:
                return -0.5 * self.params.cell_size
            if mesh_index == mesh_count - 1:
                return (cell_count - 0.5) * self.params.cell_size
            return (mesh_index - 1) * self.params.cell_size

        with mesh_path.open("w", encoding="ascii", newline="\n") as mesh:
            for x in range(mesh_count):
                sample_x = sample_index(x)
                for y in range(mesh_count):
                    sample_y = sample_index(y)
                    mesh.write(
                        f"v {vertex_coordinate(x):.6f} "
                        f"{vertex_coordinate(y):.6f} "
                        f"{float(heights[sample_x, sample_y]):.6f}\n"
                    )
            for x in range(mesh_count):
                for y in range(mesh_count):
                    mesh.write(
                        f"v {vertex_coordinate(x):.6f} "
                        f"{vertex_coordinate(y):.6f} "
                        f"{bottom_height:.6f}\n"
                    )

            for x in range(mesh_count - 1):
                for y in range(mesh_count - 1):
                    a = top_index(x, y)
                    b = top_index(x + 1, y)
                    c = top_index(x + 1, y + 1)
                    d = top_index(x, y + 1)
                    mesh.write(f"f {a} {b} {c}\nf {a} {c} {d}\n")

                    bottom_a = bottom_index(x, y)
                    bottom_b = bottom_index(x + 1, y)
                    bottom_c = bottom_index(x + 1, y + 1)
                    bottom_d = bottom_index(x, y + 1)
                    mesh.write(
                        f"f {bottom_a} {bottom_c} {bottom_b}\n"
                        f"f {bottom_a} {bottom_d} {bottom_c}\n"
                    )

            for y in range(mesh_count - 1):
                mesh.write(
                    f"f {top_index(0, y)} {top_index(0, y + 1)} "
                    f"{bottom_index(0, y + 1)} {bottom_index(0, y)}\n"
                    f"f {top_index(mesh_count - 1, y + 1)} "
                    f"{top_index(mesh_count - 1, y)} "
                    f"{bottom_index(mesh_count - 1, y)} "
                    f"{bottom_index(mesh_count - 1, y + 1)}\n"
                )
            for x in range(mesh_count - 1):
                mesh.write(
                    f"f {top_index(x + 1, 0)} {top_index(x, 0)} "
                    f"{bottom_index(x, 0)} {bottom_index(x + 1, 0)}\n"
                    f"f {top_index(x, mesh_count - 1)} "
                    f"{top_index(x + 1, mesh_count - 1)} "
                    f"{bottom_index(x + 1, mesh_count - 1)} "
                    f"{bottom_index(x, mesh_count - 1)}\n"
                )
        return mesh_path

    def _create_terrain_visual(self, mesh_path: Path, revision: int) -> str | None:
        """Spawn one static, visual-only mesh model in the Gazebo world."""
        model_name = f"soil_field_visual_{revision}"
        escaped_mesh_uri = escape(mesh_path.as_uri())
        sdf = f"""<sdf version='1.9'>
  <model name='{model_name}'>
    <pose>{self.params.origin[0]} {self.params.origin[1]} 0 0 0 0</pose>
    <static>true</static>
    <link name='terrain_link'>
      <visual name='terrain_visual'>
        <cast_shadows>true</cast_shadows>
        <geometry><mesh><uri>{escaped_mesh_uri}</uri></mesh></geometry>
        <material>
          <ambient>0.42 0.25 0.11 1</ambient>
          <diffuse>0.55 0.34 0.16 1</diffuse>
          <specular>0.05 0.05 0.05 1</specular>
        </material>
      </visual>
    </link>
  </model>
</sdf>"""
        request = EntityFactory()
        request.sdf = sdf
        transport_ok, response = self.gz_node.request(
            self.gz_create_service,
            request,
            EntityFactory,
            Boolean,
            1000,
        )
        if not transport_ok or not response.data:
            self.get_logger().error(
                f"Gazebo failed to create terrain visual {model_name}"
            )
            return None
        return model_name

    def _remove_terrain_visual(self, model_name: str) -> bool:
        request = Entity()
        request.name = model_name
        request.type = Entity.MODEL
        transport_ok, response = self.gz_node.request(
            self.gz_remove_service,
            request,
            Entity,
            Boolean,
            1000,
        )
        if not transport_ok or not response.data:
            self.get_logger().error(
                f"Gazebo failed to remove obsolete terrain visual {model_name}"
            )
            return False
        return True

    def _update_terrain_visual(self) -> None:
        """Replace the visible terrain mesh when the grid has changed."""
        obsolete_visuals = [
            name for name in self._terrain_visuals
            if name != self._current_visual_name
        ]
        for name in obsolete_visuals:
            if self._remove_terrain_visual(name):
                self._terrain_visuals.pop(name).unlink(missing_ok=True)

        with self._grid_lock:
            if not self.grid.should_update_visuals:
                return
            heights = self.grid.grid.copy()
            self.grid.should_update_visuals = False

        self._mesh_revision += 1
        mesh_path = self._write_terrain_mesh(heights, self._mesh_revision)
        model_name = self._create_terrain_visual(mesh_path, self._mesh_revision)
        if model_name is None:
            mesh_path.unlink(missing_ok=True)
            with self._grid_lock:
                self.grid.should_update_visuals = True
            return

        self._terrain_visuals[model_name] = mesh_path
        self._current_visual_name = model_name

    def cleanup(self) -> None:
        """Remove spawned terrain visuals when the ROS node exits."""
        for model_name, mesh_path in tuple(self._terrain_visuals.items()):
            if self._remove_terrain_visual(model_name):
                mesh_path.unlink(missing_ok=True)
                self._terrain_visuals.pop(model_name)
        if not self._terrain_visuals:
            self._mesh_directory.rmdir()



### SoilNode ###


def main(args=None):
    rclpy.init(args=args)

    soil_node = SoilNode()

    try:
        rclpy.spin(soil_node)
    finally:
        soil_node.cleanup()
        soil_node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()