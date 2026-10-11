docker run --rm \
  -v $(pwd):/Autonomous-Earthworks-Simulator \
  -v /tmp/.X11-unix:/tmp/.X11-unix:ro \
  -e DISPLAY=$DISPLAY \
  -e GZ_SIM_RESOURCE_PATH=${GZ_SIM_RESOURCE_PATH}:$(pwd) \
  -it liamhearderdev/earthworks \
  /bin/bash