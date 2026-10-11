#!/usr/bin/env python3

# This is where the code for the deformable soil terrain system will be placed.


from gz.transport13 import Node
from gz.msgs10.pose_v_pb2 import Pose_V
import numpy as np


class SoilFieldManager:
    def __init__(self, gz_name: str, size_x: int, size_y: int, 
                 max_height: float, cell_size: float, world_origin: list[float]):
        """ Generates a Soil Field.
        Args:
            gz_name (str): The name of the soil field's model in Gazebo Harmonic.
            size_x (int): The number of cells in the x direction.
            size_y (int): The number of cells in the y direction.
            max_height (float): The maximum height of the soil field.
            cell_size (float): The size of each cell in meters.
            world_origin (list[float]): The origin of the soil field in world 
                coordinates. Arranged as [x, y, z] .
        """

        self.name = gz_name
        self.size_x = size_x
        self.size_y = size_y
        self.cell_size = cell_size
        self.world_origin = world_origin


        model_node = Node()
        topic

        self.grid = np.array(
            [[max_height/2 for _ in range(size_y)] for _ in range(size_x)]
            )


        

        
        
### SoilField ###


def main():


    soil_field = SoilFieldManager(
        gz_name="soil_field",
        size_x=100, 
        size_y=100, 
        max_height=3.0,
        cell_size=1.0,
        )


    return

if __name__ == '__main__':
    main()