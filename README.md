# Autonomous-Earthworks-Simulator

## How to launch the excavator world
1. Configure and build the project:
    ```bash
    cmake -S . -B build && cmake --build build
    ```

2. Navigate to the project directory.

3. Set your Gazebo simulation resource path to the working directory:
    ```bash
    export GZ_SIM_RESOURCE_PATH=${GZ_SIM_RESOURCE_PATH}:$(pwd)
    ```

4. Open Gazebo and load the test world:
    ```bash
    gz sim worlds/ae_test.sdf
    ```
