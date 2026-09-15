This is a guide to installing **Gazebo Harmonic**.

 
A list of all resources used can be found here: 

https://gazebosim.org/home 

https://gazebosim.org/docs/harmonic/getstarted/ 

https://gazebosim.org/docs/harmonic/ros_installation/ 

https://docs.ros.org/en/jazzy/Installation/Ubuntu-Install-Debs.html 

https://gazebosim.org/docs/harmonic/install_ubuntu/ 

 
Basic steps (for a **Windows** user): 

- Set up WSL on your machine. 

- Set up Ubuntu-24.04 using WSL. 

- Run Ubuntu-24.04 through WSL. 

- Follow this ( https://gazebosim.org/docs/harmonic/install_ubuntu/ ) to install Gazebo Harmonic on Ubuntu. 

- Follow this ( https://gazebosim.org/docs/harmonic/getstarted/ ) to learn to run Gazebo Harmonic. 

Notes: 

**Do NOT** try to run through a VM. Gazebo needs direct interfaces with your machine’s hardware, so a VM will cause Gazebo to run incredibly slowly.


**macOS setup** — **ARM64** development environment

Platform status: macOS on Apple Silicon is supported as a best-effort development environment. The agreed deployment and testing platform for this project is Ubuntu 24.04 AMD64. Changes developed on macOS must be verified on Ubuntu before being considered complete.

**Prerequisites**  
Install Apple’s command-line development tools:

xcode-select --install
Install Homebrew if it is not already installed.

Install the required development tools:

brew install git git-lfs cmake ninja eigen pkg-config
Install Gazebo Harmonic
brew tap osrf/simulation
brew trust osrf/simulation
brew install gz-harmonic
Verify the installation:

gz sim --version
The output should report Gazebo Sim version 8, which corresponds to Gazebo Harmonic.

**Run Gazebo on macOS**  
Gazebo must be started using two Terminal windows on macOS.

In the first Terminal, start the simulation server:

gz sim --force-version 8 -v 4 shapes.sdf -s
Leave this process running.

In a second Terminal, start the graphical interface:

gz sim --force-version 8 -v 4 -g
Stop either process by selecting its Terminal window and pressing Control+C.

Successful operation on macOS does not replace Ubuntu 24.04 AMD64 acceptance testing.

**Remove the macOS installation**  
brew uninstall gz-harmonic
brew untap osrf/simulation
brew autoremove
brew cleanup