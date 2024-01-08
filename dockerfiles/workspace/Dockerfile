FROM osrf/ros:humble-desktop

# Add vscode user with same UID and GID as your host system
# (copied from https://code.visualstudio.com/remote/advancedcontainers/add-nonroot-user#_creating-a-nonroot-user)
ARG USERNAME=vscode
ARG USER_UID=1000
ARG USER_GID=$USER_UID

# ZED SDK Install
# RUN apt-get update -y || true ; apt-get install --no-install-recommends lsb-release wget less zstd udev sudo python3 python3-pip libpng-dev libgomp1 -y ; \
#     python3 -m pip install numpy opencv-python ; \
#     wget -q -O ZED_SDK.run https://download.stereolabs.com/zedsdk/4.0/cu121/ubuntu22  \
#     && chmod +x ZED_SDK.run \
#     && ./ZED_SDK.run -- silent skip_cuda skip_od_module skip_hub\
#     && rm ZED_SDK.run \
#     && rm -rf /var/lib/apt/lists/*
    
RUN groupadd --gid $USER_GID $USERNAME \
    && useradd -s /bin/bash --uid $USER_UID --gid $USER_GID -m $USERNAME \
    && apt-get update \
    && apt-get install -y sudo \
    && echo $USERNAME ALL=\(root\) NOPASSWD:ALL > /etc/sudoers.d/$USERNAME \
    && chmod 0440 /etc/sudoers.d/$USERNAME

# Install necessary packages and utilities
RUN apt-get update && apt-get install -y \
    git \
    joystick \
    jstest-gtk \
    evtest \
    ros-humble-gazebo-ros-pkgs \
    ros-humble-gazebo-ros2-control \
    ros-humble-ros2-control \
    ros-humble-controller-manager \
    ros-humble-robot-state-publisher \
    ros-humble-xacro \
    ros-humble-rviz2 \
    ros-humble-gazebo-plugins \
    ros-humble-joint-state-publisher-gui \
    ros-humble-rosbridge-suite \
    ros-humble-twist-mux \
    ros-humble-robot-localization \
    ros-humble-navigation2 \
    ros-humble-nav2-bringup \
    ros-humble-mapviz \
    ros-humble-ros2-controllers \
    && rm -rf /var/lib/apt/lists/*

# Switch from root to user
USER $USERNAME

# Add user to video group to allow access to webcam
RUN sudo usermod --append --groups video $USERNAME

# Update all packages
RUN sudo apt update && sudo apt upgrade -y

# Install Git
RUN sudo apt install -y git

# Update and source ROS setup files
RUN echo "source /opt/ros/${ROS_DISTRO}/setup.bash" >> ~/.bashrc \
    && echo "source /usr/share/colcon_argcomplete/hook/colcon-argcomplete.bash" >> ~/.bashrc \
    && echo "source /sdrc_ws/install/setup.bash" >> ~/.bashrc  # Replace /sdrc_ws with your workspace name

# Rosdep update
RUN rosdep update