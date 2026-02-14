import rclpy
from rclpy.node import Node
from nav2_simple_commander.robot_navigator import BasicNavigator
from geometry_msgs.msg import PoseStamped
from std_msgs.msg import String

class NavigateToPose(Node):
    def __init__(self):
        super().__init__("navigate_to_pose")
        self.navigator = BasicNavigator()
        self.status = String()
        self.status.data = "RUNNING"

    def execute(self, inputs):
        try:
            # Extract pose from inputs
            pose = inputs["pose"]  # Expected: PoseStamped

            self.navigator.goToPose(pose)

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
            self.get_logger().error(f"NavigateToPose failed: {str(e)}")
            self.status.data = "FAILURE"

        return self.status.data
