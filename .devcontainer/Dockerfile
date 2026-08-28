FROM ros:jazzy-ros-base-noble

ENV GZ_VERSION=harmonic


RUN apt-get update && apt-get install -y \
    build-essential \
    clang-format \
    clang-tidy \
    cmake \
    cppcheck \
    gdb \
    git \
    ninja-build \
    pkg-config \
    python3-colcon-common-extensions \
    python3-rosdep \
    python3-setuptools \
    ros-jazzy-ros-gz \
    ros-jazzy-ros-gz-bridge \
    ros-jazzy-robot-state-publisher \
    ros-jazzy-joint-state-publisher \
    ros-jazzy-xacro \
    ros-jazzy-teleop-twist-keyboard

# Make ROS 2 commands available in every terminal.
RUN echo "source /opt/ros/jazzy/setup.bash" >> /root/.bashrc
