# SDRC_URC2025

Source Code for the Rover Competing in University Rover Challenge 2025

## Stuff To Install 

1. Slam Tool Box    

```
sudo apt install ros-humble-slam-toolbox
```  

2. Joystick/remote control  

```
sudo apt install joystick jstest-gtk evtest
```   


## How To Collaborate

### 1. Setup Your ROS 2 Workspace

1. Create a ROS 2 workspace if you haven't already with a src directory

2. Navigate to the `src` directory and clone the repository:

```

sudo git clone https://github.com/Sun-Devil-Robotics-Club/URC_2025_SRC_Code.git .

```

### 2. Create and Work on a New Branch

1. Create a new branch (replace `<branch_name>` with your desired branch name):

```

git checkout -b <branch_name>

```

2. Make and save your changes.

3. Stage your changes:

```

git add .

```

4. Commit your changes (replace `<your_message>` with a meaningful commit message):

```

git commit -m "<your_message>"

```

5. Push your changes to the repository:

```

git push origin <branch_name>

```

### 3. Open a Pull Request

After pushing your changes, go to the GitHub repository and open a pull request. This will allow your changes to be reviewed by the team and, if approved, merged into the main codebase.

## Build your Enviornment  

Now that your ros2 workspace is already setup you should have a file structure that has `<workspace_name>\src`. In src make sure you have all of the packages in this repository.

1. Go into your ros2 workspace directory. You can do this by running this command in from the root directory  

```

cd <workspace_name>
```  

2. Then run colcon build (make sure you are running this from your ros2 workspace not in the src directory)
```

colcon build
```

3. If you run into any errors let me know and we will figure it out. You are likely missing some dependencies so make sure you have followed the commands in Part 1 of this read me ## Stuff to install

### Run Example Simulation

1. Source your workspace  
```

source ~/<workspace_name>/install/setup.bash
```

2. In a terminal run the following command. This will start the simulation and rviz you should see a world show up with some objects in it and the robot
```

ros2 launch sdrc_bringup sdrc_gazebo.launch.py use_ros2_control:=false
```

3. To control the rover run; this should bring up a control pad in the terminal that allow syou to control the rover using u,i,o,j,k,l,m,",",".","/"
```

ros2 teleop_twist_keyboard teleop_twist_keyboard
```
