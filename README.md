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
