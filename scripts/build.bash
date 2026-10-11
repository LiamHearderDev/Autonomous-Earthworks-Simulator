#!/bin/bash
source /opt/ros/jazzy/setup.bash || exit 1
cd excavator/ || exit 1
rm -rf build/ install/ log/
colcon build --symlink-install
source install/setup.bash
cd ..
echo "Build complete!"