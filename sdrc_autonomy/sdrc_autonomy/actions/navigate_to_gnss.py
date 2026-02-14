import rclpy
from rclpy.node import Node
from nav2_simple_commander.robot_navigator import BasicNavigator
from geometry_msgs.msg import PoseStamped
import utm
from std_msgs.msg import String

class NavigateToGNSS(Node):
    def __init__(self):
        super().__init__("navigate_to_gnss")
        self.navigator = BasicNavigator()
        self.status = String()
        self.status.data = "RUNNING"

    def execute(self, inputs):
        try:
            # Extract GNSS waypoint (lat, lon) from inputs
            lat, lon = inputs["waypoint"]  # Expected format: (lat, lon)
            utm_coords = utm.from_latlon(lat, lon)

            # Create a PoseStamped in the map frame
            goal_pose = PoseStamped()
            goal_pose.header.frame_id = "map"
            goal_pose.pose.position.x = utm_coords[0]
            goal_pose.pose.position.y = utm_coords[1]
            goal_pose.pose.orientation.w = 1.0  # Default orientation

            self.navigator.goToPose(goal_pose)

            # Wait for completion
            while not self.navigator.isTaskComplete():
                feedback = self.navigator.getFeedback()
                self.get_logger().info(f"Distance remaining: {feedback.distance_remaining:.2f} meters")
                rclpy.spin_once(self)
                self.status.data = "RUNNING"

            # Check result
            if self.navigator.isTaskComplete():
                self.status.data = "SUCCESS"
            else:
                self.status.data = "FAILURE"

        except Exception as e:
            self.get_logger().error(f"NavigateToGNSS failed: {str(e)}")
            self.status.data = "FAILURE"

        return self.status.data
