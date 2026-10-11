First Idea:
- A C++ system plugin
- Use a system plugin that owns a soil patch as a 2D array, and computes forces from it. The actual Gazebo Collision and rendering geometry stay simple and only get updated occasionally.
- Structure
    - A system plugin with:
	    - A height array, e.g. 200x200, with a cell size and origin
		- Pass in things like the bucket, origin, etc, as plugin parameters.
	- The actual soil itself would use the SDF collision bitmask feature to ensure that it will normally collide with everything in the scene EXCEPT the bucket which will have no collision with it.

Second Idea:
- A Python node.
- Owns a 2D array, and listens to ROS/Gz topics to determine the world positions of each element.
- Structure:
    - Everything is basically the same as the first idea, but now we update visuals by writing an OBJ/DAE and swapping the visuals using the create/remove services.
    - Perhaps can creat a mesh using `Trimesh`?


Per-step loop?
1. Read the bucket's world pos, then transform a few fixed points along the bucket's edge (to ensure it's tilt independent).
2. look up terrain height at each point's (x, y) with bilinear interpolation
3. Check the bucket's penetration height at that point.
4. Compute the soil's resistive force.
5. Apply resistive force to the bucket.
6. Remove material by lowering the cells under the tooth. 
7. Add the removed volume to a bucket_payload counter. 

Dumping?
- When the bucket is rotated past a threshold angle and the payload > 0, deposit the payload into cells around the bucket's ground projection.
- The heights of the nearby cells would be increased, and the bucket's payload counter would be decreased.


# Classes
## SoilParams
- A dataclass that contains all of the data required by this system.

## HeightGrid
- A NumPy heightfield. Handles bilinear lookup, cutting a cell down (which returns removed volumed), and raising a cell up.

## SoilModel
- Designed to handle physics updates, and visual model changes.

## SoilNode
- The only part that imports ROS. This is to ensure adequate testing can take place without needing to launch Gazebo.
- Subscribes to bucket pose, estimates velocity by finite difference, and publishes a Wrench.