#!/usr/bin/env python3

# This is where the code for the deformable soil terrain system will be placed.

import rclpy
from rclpy.node import Node as RosNode

from gz.transport13 import GzNode
from gz.msgs10.pose_v_pb2 import Pose_V     # Vector of poses
import numpy as np


class SoilParams:
    """ Contains all of the data required by the SoilFieldManager. """

    # TODO: Make these adjustable via ROS params, perhaps
    grid_cells: int = 25            # cells per side
    cell_size: float = 1.0          # metres
    origin: tuple = (0.0, 0.0)      # world (x,y) of cell [0,0]
    base_height: float = 0.0        # initial terrain height
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

    def to_local_coords(self, x, y) -> tuple[int, int]:
        """ Converts a world position (x,y) to a local grid cell. Does not
        check if the result is out of bounds. """
        cell_x = (x - self.params.origin[0]) / self.params.cell_size
        cell_y = (y - self.params.origin[1]) / self.params.cell_size
        return cell_x, cell_y

    def is_in_bounds(self, x, y) -> bool:
        """ Checks if, given an (x,y) world coordinate, a world location is
        within the bounds of the grid. """
        cell_x, cell_y = self.to_local_coords(x, y)

        cell_count = self.params.grid_cells
        return (0 <= cell_x < cell_count - 1) and (0 <= cell_y < cell_count - 1)


    def lower_height(self, x, y, new_height) -> float:
        """ Lowers the height of a cell at world location (x,y) to a new
        height value. Returns the removed volume in m^3 """

        if not self.is_in_bounds(x, y):
            return 0.0
        
        cell_x, cell_y = self.to_local_coords(x, y)
        closest_x, closest_y = int(round(cell_x)), int(round(cell_y))

        old_height = float(self.grid[closest_x][closest_y])
        if new_height >= old_height:
            return 0.0

        self.grid[closest_x][closest_y] = new_height
        self.should_update_visuals = True
        return (old_height - new_height) * self.params.cell_size ** 2


    def deposit(self, x, y, volume) -> None:
        """ Adds volume to a specific (x,y) location. """
        if not self.is_in_bounds(x, y) or volume <= 0.0:
            return

        cell_x, cell_y = self.to_local_coords(x, y)
        closest_x, closest_y = int(round(cell_x)), int(round(cell_y))
        self.grid[closest_x][closest_y] += volume / self.params.cell_size ** 2
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
        return



### SoilModel ###          



class SoilNode(RosNode):
    """ Subscribes to bucket pose, estimates velocity by finite 
    difference, and publishes a Wrench. """

    def __init__(self):
        super().__init__('soil_node')
        self.params = SoilParams()
        self.grid = HeightGrid(self.params)
        self.model = SoilModel(self.params, self.grid)

        # TODO: Get info about things like world position here

        # TODO: Get the name of the current environment

        # TODO: Subscribe to the environment pose topic

        # TODO: Create a timer that runs a physics step, and another that runs a
        #   visual step. 
    pass

### SoilNode ###


def main(args=None):



    # soil_node = SoilNode(
    #     gz_name="soil_field",
    #     size_x=100, 
    #     size_y=100, 
    #     max_height=3.0,
    #     cell_size=1.0,
    #     )


    return

if __name__ == '__main__':
    main()