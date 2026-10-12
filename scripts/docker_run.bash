docker run --rm \
  -v $(pwd):/Autonomous-Earthworks-Simulator \
  -v /tmp/.X11-unix:/tmp/.X11-unix:ro \
  -e DISPLAY=$DISPLAY \
  -e GZ_SIM_RESOURCE_PATH=${GZ_SIM_RESOURCE_PATH}:/Autonomous-Earthworks-Simulator/models:/Autonomous-Earthworks-Simulator/worlds:/Autonomous-Earthworks-Simulator/ \
  -w /Autonomous-Earthworks-Simulator \
  -it liamhearderdev/earthworks \
  /bin/bash