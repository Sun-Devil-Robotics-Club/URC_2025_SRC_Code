import rclpy
from rclpy.node import Node
from nav2_simple_commander.robot_navigator import BasicNavigator
from tf2_geometry_msgs import PointStamped, PoseStamped
import tf2_ros
from rclpy.duration import Duration
import utm

import math
from geometry_msgs.msg import Quaternion


def quaternion_from_euler(roll, pitch, yaw):
    cy = math.cos(yaw * 0.5)
    sy = math.sin(yaw * 0.5)
    cp = math.cos(pitch * 0.5)
    sp = math.sin(pitch * 0.5)
    cr = math.cos(roll * 0.5)
    sr = math.sin(roll * 0.5)

    q = Quaternion()
    q.w = cy * cp * cr + sy * sp * sr
    q.x = cy * cp * sr - sy * sp * cr
    q.y = sy * cp * sr + cy * sp * cr
    q.z = sy * cp * cr - cy * sp * sr
    return q


def latLonYaw2UTMPose(utm_coords: tuple, yaw: float = 0.0):
    goal_pose = PoseStamped()
    goal_pose.header.frame_id = "utm"

    goal_pose.pose.position.x = utm_coords[0]
    goal_pose.pose.position.y = utm_coords[1]
    goal_pose.pose.orientation = quaternion_from_euler(0.0, 0.0, yaw)
    return goal_pose


class InteractiveGpsWpCommander(Node):
    """
    ROS2 node to send gps waypoints to nav2 received from mapviz's point click publisher
    """

    def __init__(self):
        super().__init__(node_name="gps_wp_commander")
        self.navigator = BasicNavigator("basic_navigator")
        self.tf_buffer = tf2_ros.Buffer()
        self.listener = tf2_ros.TransformListener(self.tf_buffer, self)
        self.mapviz_wp_sub = self.create_subscription(
            PointStamped, "/clicked_point", self.mapviz_wp_cb, 1
        )

    def transform_utm_pose_to_map_pose(self, utm_pose: PoseStamped):
        try:
            transform = self.tf_buffer.lookup_transform("map", "utm", rclpy.time.Time())
            map_pose = self.tf_buffer.transform(utm_pose, "map")
            return map_pose
        except (
            tf2_ros.LookupException,
            tf2_ros.ConnectivityException,
            tf2_ros.ExtrapolationException,
        ) as e:
            self.get_logger().error(f"Error in transforming pose: {e}")
            return None

    def mapviz_wp_cb(self, msg: PointStamped):
        """
        clicked point callback, sends received point to nav2 gps waypoint follower if its a geographic point
        """
        if msg.header.frame_id != "wgs84":
            self.get_logger().warning(
                "Received point from mapviz that ist not in wgs84 frame. This is not a gps point and wont be followed"
            )
            return

        utm_coords = utm.from_latlon(latitude=msg.point.y, longitude=msg.point.x)
        self.get_logger().info(f"{utm_coords}")

        utm_pose = latLonYaw2UTMPose(utm_coords)

        map_pose = self.transform_utm_pose_to_map_pose(utm_pose)
        self.get_logger().info(
            f"Successfully transformed map pose x: {map_pose.pose.position.x}, {map_pose.pose.position.y}, {map_pose.pose.position.z}"
        )


        self.navigator.followWaypoints([map_pose])
        if (self.navigator.isTaskComplete()):
            self.get_logger().info("wps completed successfully")


def main():
    rclpy.init()
    gps_wpf = InteractiveGpsWpCommander()
    rclpy.spin(gps_wpf)


if __name__ == "__main__":
    main()
