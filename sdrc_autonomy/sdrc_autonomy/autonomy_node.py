import rclpy
from rclpy.node import Node
from nav2_simple_commander.robot_navigator import BasicNavigator
from geometry_msgs.msg import PoseStamped
import time

class AutonomyNode(Node):
    def __init__(self):
        super().__init__("autonomy_node")
        self.navigator = BasicNavigator()
        self.get_logger().info("Autonomy Node Initialized")

    def move_to_waypoint(self, x, y, yaw=0.0):
        """Send a waypoint goal to Nav2"""
        goal_pose = PoseStamped()
        goal_pose.header.frame_id = "map"
        goal_pose.pose.position.x = x
        goal_pose.pose.position.y = y
        goal_pose.pose.orientation.w = 1.0  # Facing forward

        self.navigator.goToPose(goal_pose)

        # Wait for completion
        while not self.navigator.isTaskComplete():
            feedback = self.navigator.getFeedback()
            self.get_logger().info(f"Distance remaining: {feedback.distance_remaining:.2f} meters")
            time.sleep(1)

        self.get_logger().info("Arrived at waypoint!")

    def move_to_goal(self, pose):
        self.navigator.goToPose(pose)
        while not self.navigator.isTaskComplete():
            feedback = self.navigator.getFeedback()
            if feedback.distance_remaining <= 2.0:      # Custom stopping condition
                self.navigator.cancelTask()
                self.get_logger().info("Stopped within 2 meters!")
            break
        time.sleep(0.5)

    def run_mission(self):
        """Mission execution logic"""
        self.get_logger().info("Starting mission...")

        # Move to Sample Site
        self.move_to_waypoint(5.0, 5.0)
        
        # (Future: Add Sample Collection Logic Here)

        # Return to Base
        self.move_to_waypoint(0.0, 0.0)

        self.get_logger().info("Mission Complete!")


def main():
    rclpy.init()
    node = AutonomyNode()
    node.run_mission()
    node.destroy_node()
    rclpy.shutdown()

if __name__ == "__main__":
    main()
