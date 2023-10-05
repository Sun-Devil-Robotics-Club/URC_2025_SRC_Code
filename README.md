# SDRC_URC2025

This repository contains the source code for the rover competing in the University Rover Challenge 2025 by the Sun Devil Robotics Club.

## 📦 Prerequisites & Installation

Before you start, make sure to install the following packages:

### 1. Slam Tool Box
```
sudo apt install ros-humble-slam-toolbox
```

### 2. Joystick/Remote Control
```
sudo apt install joystick jstest-gtk evtest
```

### 3. Gazebo Dependencies
```
sudo apt install ros-humble-gazebo-ros-pkgs
sudo apt install ros-humble-ros2-control
sudo apt install ros-humble-controller-manager
sudo apt install ros-humble-robot-state-publisher
sudo apt install ros-humble-xacro
sudo apt install ros-humble-rviz2
sudo apt install ros-humble-gazebo-plugins
sudo apt install ros-humble-joint-state-publisher-gui
```

### 4. Zed 2 Dependencies   

## 1. Install ZED SDK for Ubuntu 22.04

## 2. Dependencies  
```
rosdep install --from-paths src --ignore-src -r -y
```
## 🤝 How to Collaborate

### 1. Setup Your ROS 2 Workspace
- Create a ROS 2 workspace if you haven't already, with a `src` directory.
- Navigate to the `src` directory and clone the repository:
```
sudo git clone https://github.com/Sun-Devil-Robotics-Club/URC_2025_SRC_Code.git .
```

### 2. Create and Work on a New Branch
- Create a new branch (replace `<branch_name>` with your desired branch name):
```
git checkout -b <branch_name>
```
- Make and save your changes, then stage them:
```
git add .
```
- Commit your changes (replace `<your_message>` with a meaningful commit message):
```
git commit -m "<your_message>"
```
- Push your changes to the repository:
```
git push origin <branch_name>
```

### 3. Open a Pull Request
After pushing your changes, go to the GitHub repository and open a pull request. Your changes will be reviewed by the team and, if approved, merged into the main codebase.

## 🛠️ Build Your Environment

Once your ROS 2 workspace is set up, ensure you have a file structure that has `<workspace_name>\src` and that all of the packages in this repository are present in the `src` directory.

- Navigate to your ROS 2 workspace directory:
```
cd <workspace_name>
```
- Then run colcon build (ensure this is run from your ROS 2 workspace, not the `src` directory):
```
colcon build
```

If any errors arise, you are likely missing some dependencies, so make sure you have followed the installation commands mentioned above.

## 🚀 Run Example Simulation

1. Source your workspace:
```
source ~/<workspace_name>/install/setup.bash
```
2. Start the simulation and RViz in a terminal. You should see a world populated with objects and the robot:
```
ros2 launch sdrc_bringup sdrc_gazebo.launch.py use_ros2_control:=false
```
3. To control the rover, run the following command. This will bring up a control pad in the terminal, allowing you to control the rover using `u,i,o,j,k,l,m,",",".","/":
```
ros2 teleop_twist_keyboard teleop_twist_keyboard
```

## ✉️ Contact & Support

If you run into any issues or have questions, feel free to contact the project maintainers or raise an issue on the repository. Your contributions and feedback are highly appreciated.

Happy Coding!
