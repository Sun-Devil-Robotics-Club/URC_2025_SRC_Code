#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import PoseStamped
from nav2_simple_commander.robot_navigator import BasicNavigator
import py_trees
from py_trees.common import Status


class IsTargetVisible(py_trees.behaviour.Behaviour):
    """Condition: Check if target pose is available."""

    def __init__(self, name, node: Node):
        super().__init__(name)
        self.node = node
        self.blackboard = self.attach_blackboard_client()
        self.blackboard.register_key("target_pose", access=py_trees.common.Access.READ)

    def update(self):
        try:
            pose = self.blackboard.get("target_pose")
            if pose is not None:
                age = (
                    self.node.get_clock().now()
                    - rclpy.time.Time.from_msg(pose.header.stamp)
                ).nanoseconds / 1e9
                if age < 2.0:  # Fresh detection within 2 seconds
                    return Status.SUCCESS
        except KeyError:
            pass
        return Status.FAILURE


class NavigateToTarget(py_trees.behaviour.Behaviour):
    """Action: Navigate to detected target."""

    def __init__(self, name, node: Node, navigator: BasicNavigator):
        super().__init__(name)
        self.node = node
        self.navigator = navigator
        self.blackboard = self.attach_blackboard_client()
        self.blackboard.register_key("target_pose", access=py_trees.common.Access.READ)
        self.goal_sent = False

    def initialise(self):
        self.goal_sent = False

    def update(self):
        if not self.goal_sent:
            try:
                pose = self.blackboard.get("target_pose")
                self.navigator.goToPose(pose)
                self.goal_sent = True
                self.node.get_logger().info("Sent navigation goal to detected target")
            except KeyError:
                return Status.FAILURE

        if not self.navigator.isTaskComplete():
            return Status.RUNNING

        result = self.navigator.getResult()
        return Status.SUCCESS if result else Status.FAILURE


class NavigateToGPS(py_trees.behaviour.Behaviour):
    """Action: Navigate to GPS waypoint."""

    def __init__(self, name, node: Node, navigator: BasicNavigator, gps_pose: PoseStamped):
        super().__init__(name)
        self.node = node
        self.navigator = navigator
        self.gps_pose = gps_pose
        self.goal_sent = False

    def initialise(self):
        self.goal_sent = False

    def update(self):
        if not self.goal_sent:
            self.navigator.goToPose(self.gps_pose)
            self.goal_sent = True
            self.node.get_logger().info("Navigating to GPS waypoint")

        if not self.navigator.isTaskComplete():
            return Status.RUNNING

        return Status.SUCCESS if self.navigator.getResult() else Status.FAILURE


class AutonomyBTNode(Node):
    def __init__(self):
        super().__init__("autonomy_bt_node")
        self.navigator = BasicNavigator()

        # Subscribe to localized targets
        self.target_sub = self.create_subscription(
            PoseStamped, "/autonomy/target_pose", self.target_callback, 10
        )

        # Blackboard for sharing data between BT nodes
        self.blackboard = py_trees.blackboard.Client()
        self.blackboard.register_key("target_pose", access=py_trees.common.Access.WRITE)

        # Build behavior tree
        self.tree = self.create_tree()

        # Tick tree at 10 Hz
        self.timer = self.create_timer(0.1, self.tick_tree)
        self.get_logger().info("Autonomy BT initialized")

    def target_callback(self, msg):
        """Update blackboard when new target is detected."""
        self.blackboard.set("target_pose", msg)
        self.get_logger().info("Target pose updated in blackboard")

    def create_tree(self):
        """Build the behavior tree structure."""
        gps_wp1 = PoseStamped()
        gps_wp1.header.frame_id = "map"
        gps_wp1.pose.position.x = 10.0
        gps_wp1.pose.position.y = 10.0
        gps_wp1.pose.orientation.w = 1.0

        root = py_trees.composites.Sequence("Mission", memory=False)

        # Leg 1: Try visual approach, fall back to GPS
        leg1 = py_trees.composites.Selector("Leg1", memory=False)

        visual_approach = py_trees.composites.Sequence("VisualApproach", memory=False)
        visual_approach.add_children(
            [
                IsTargetVisible("CheckTarget", self),
                NavigateToTarget("GoToTarget", self, self.navigator),
            ]
        )

        gps_approach = NavigateToGPS("GPSNavigation", self, self.navigator, gps_wp1)

        leg1.add_children([visual_approach, gps_approach])
        root.add_child(leg1)

        return py_trees.trees.BehaviourTree(root)

    def tick_tree(self):
        """Execute one tick of the behavior tree."""
        self.tree.tick()


def main(args=None):
    rclpy.init(args=args)
    node = AutonomyBTNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
