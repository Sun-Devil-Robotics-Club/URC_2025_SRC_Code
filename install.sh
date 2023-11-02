#!/bin/bash

if ! command -v docker &> /dev/null; then
    echo "Docker is not installed. Please install Docker and try again."
    exit 1
fi

image_name="tiryoh/ros2-desktop-vnc"
image_tag="humble"


get_cwd() {
    local current_dir="$(pwd)"
    
    local parent_dir="$(dirname "$current_dir")"

    if [[ "$(uname -s)" == "Darwin" || "$(uname -s)" == "Linux" ]]; then
        echo "$parent_dir"
    elif [[ "$(uname -s)" == *"MINGW"* || "$(uname -s)" == *"MSYS"* ]]; then
        dir="$(dirname "$(dirname "$(readlink -f "$BASH_SOURCE")")" | sed 's/^[A-Za-z]://')"
        echo "/$(echo "$dir" | sed 's/\\/\//g' | sed 's/://')"
    else
        echo "Unsupported platform: $(uname -s)"
        exit 1
    fi
}

container_name="sdrc_container"
mount_dir=$(get_cwd)

start_container() {

    if docker ps -q --filter "name=$container_name" | grep -q .; then
        echo "Container $container_name is already running."
        exit 1
    fi

    existing_container=$(docker ps -aq --filter name="$container_name")
    if [[ -n "$existing_container" ]]; then
        docker start "$container_name" >/dev/null 2>&1
        echo "Container $container_name started. VNC server running on port 6060"
    else
        docker pull --platform=linux/amd64 "$image_name:$image_tag"
        docker run -p 6060:80 --shm-size=512m --security-opt seccomp=unconfined -d --name "$container_name" -v "$mount_dir:/home/ubuntu/sdrc_container" "$image_name:$image_tag"
        echo "Container $container_name pulled, created, and started. VNC Server running on port 6060"
    fi
}


start_container