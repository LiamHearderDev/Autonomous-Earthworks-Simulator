#!/bin/bash
cd excavator/
rm -r build && rm -r install && rm -r log
colcon build --symlink-install
source install/setup.bash
source /opt/ros/jazzy/setup.bash
cd ..