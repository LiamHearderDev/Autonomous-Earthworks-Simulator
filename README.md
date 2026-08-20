# Autonomous-Earthworks-Simulator


## macOS setup — ARM64 development environment

> **Platform status:** macOS on Apple Silicon is supported as a best-effort development environment. The agreed deployment and testing platform for this project is Ubuntu 24.04 AMD64. Changes developed on macOS must be verified on Ubuntu before being considered complete.

### Prerequisites

Install Apple’s command-line development tools:

```bash
xcode-select --install
```

Install [Homebrew](https://brew.sh) if it is not already installed.

Install the required development tools:

```bash
brew install git git-lfs cmake ninja eigen pkg-config
```

### Install Gazebo Harmonic

```bash
brew tap osrf/simulation
brew trust osrf/simulation
brew install gz-harmonic
```

Verify the installation:

```bash
gz sim --version
```

The output should report Gazebo Sim version 8, which corresponds to Gazebo Harmonic.

### Run Gazebo on macOS

Gazebo must be started using two Terminal windows on macOS.

In the first Terminal, start the simulation server:

```bash
gz sim --force-version 8 -v 4 shapes.sdf -s
```

Leave this process running.

In a second Terminal, start the graphical interface:

```bash
gz sim --force-version 8 -v 4 -g
```

Stop either process by selecting its Terminal window and pressing `Control+C`.

### Known limitations

- Gazebo’s graphical interface can be unstable on macOS.
- Some GUI panels and plugins may crash or behave incorrectly.
- Rendering and simulation performance may differ from Ubuntu.
- ARM64 and macOS support are provided on a best-effort basis.
- Successful operation on macOS does not replace Ubuntu 24.04 AMD64 acceptance testing.

### Remove the macOS installation

```bash
brew uninstall gz-harmonic
brew untap osrf/simulation
brew autoremove
brew cleanup
```
