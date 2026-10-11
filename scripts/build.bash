#!/bin/bash
cd excavator/ || exit 1
rm -rf build/ install/ log/
colcon build --symlink-install
source install/setup.bash
source /opt/ros/jazzy/setup.bash
cd ..