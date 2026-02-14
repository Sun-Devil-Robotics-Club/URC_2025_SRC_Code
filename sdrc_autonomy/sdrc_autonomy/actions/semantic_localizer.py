#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image, CameraInfo
from geometry_msgs.msg import PointStamped, PoseStamped
from std_msgs.msg import String
from cv_bridge import CvBridge
import numpy as np
import tf2_ros
from tf2_geometry_msgs import do_transform_point
import cv2


class SemanticLocalizer(Node):
    """
    Converts 2D bounding boxes from detection nodes into 3D navigation goals.
    Subscribes to detection outputs and publishes PoseStamped for Nav2.
    """

    def __init__(self):
        super().__init__("semantic_localizer")

        # TF2 for coordinate transforms
        self.tf_buffer = tf2_ros.Buffer()
        self.tf_listener = tf2_ros.TransformListener(self.tf_buffer, self)

        # Subscribers - connect to your detection nodes
        self.image_sub = self.create_subscription(
            Image, "/zed2i/left/image_rect_color", self.image_callback, 10
        )
        self.depth_sub = self.create_subscription(
            Image, "/zed2i/depth/depth_registered", self.depth_callback, 10
        )
        self.camera_info_sub = self.create_subscription(
            CameraInfo, "/zed2i/left/camera_info", self.camera_info_callback, 10
        )

        # Subscribe to detection outputs (from detect_ar_tag/detect_object)
        self.detection_sub = self.create_subscription(
            PointStamped, "/detected_objects/points", self.detection_callback, 10
        )

        # Publishers
        self.target_pose_pub = self.create_publisher(
            PoseStamped, "/autonomy/target_pose", 10
        )
        self.debug_pub = self.create_publisher(
            Image, "/semantic_localizer/debug_image", 10
        )

        # State
        self.bridge = CvBridge()
        self.depth_image = None
        self.camera_matrix = None
        self.dist_coeffs = None
        self.latest_rgb = None

        # Persistence filter
        self.detection_buffer = []
        self.buffer_size = 5
        self.spatial_threshold = 0.3  # meters

        self.get_logger().info("Semantic Localizer initialized")

    def camera_info_callback(self, msg):
        if self.camera_matrix is None:
            self.camera_matrix = np.array(msg.k).reshape(3, 3)
            self.dist_coeffs = np.array(msg.d)
            self.get_logger().info("Camera calibration loaded")

    def depth_callback(self, msg):
        try:
            self.depth_image = self.bridge.imgmsg_to_cv2(msg, desired_encoding="32FC1")
        except Exception as e:
            self.get_logger().error(f"Depth conversion failed: {e}")

    def image_callback(self, msg):
        try:
            self.latest_rgb = self.bridge.imgmsg_to_cv2(msg, desired_encoding="bgr8")
        except Exception as e:
            self.get_logger().error(f"RGB conversion failed: {e}")

    def detection_callback(self, msg: PointStamped):
        """
        Receives 2D pixel coordinates from detection nodes.
        Converts to 3D map coordinates.
        """
        if self.depth_image is None or self.camera_matrix is None:
            self.get_logger().warn("Depth or calibration not ready")
            return

        # Extract pixel coordinates
        center_u = int(msg.point.x)
        center_v = int(msg.point.y)

        # Validate bounds
        h, w = self.depth_image.shape[:2]
        if center_u < 0 or center_u >= w or center_v < 0 or center_v >= h:
            self.get_logger().warn(f"Detection out of bounds: ({center_u}, {center_v})")
            return

        # ROI sampling for robust depth
        kernel_size = 10
        roi_u_min = max(0, center_u - kernel_size // 2)
        roi_u_max = min(w, center_u + kernel_size // 2)
        roi_v_min = max(0, center_v - kernel_size // 2)
        roi_v_max = min(h, center_v + kernel_size // 2)

        depth_roi = self.depth_image[roi_v_min:roi_v_max, roi_u_min:roi_u_max]
        valid_depths = depth_roi[(depth_roi > 0.1) & (depth_roi < 20.0)]

        if len(valid_depths) == 0:
            self.get_logger().warn("No valid depth in ROI")
            return

        Z = float(np.median(valid_depths))

        # Pinhole camera model
        fx = self.camera_matrix[0, 0]
        fy = self.camera_matrix[1, 1]
        cx = self.camera_matrix[0, 2]
        cy = self.camera_matrix[1, 2]

        X_c = (center_u - cx) * Z / fx
        Y_c = (center_v - cy) * Z / fy
        Z_c = Z

        # Create point in camera frame
        point_camera = PointStamped()
        point_camera.header.stamp = msg.header.stamp
        point_camera.header.frame_id = "zed2i_left_camera_optical_frame"
        point_camera.point.x = X_c
        point_camera.point.y = Y_c
        point_camera.point.z = Z_c

        # Transform to map frame
        try:
            transform = self.tf_buffer.lookup_transform(
                "map",
                point_camera.header.frame_id,
                point_camera.header.stamp,
                timeout=rclpy.duration.Duration(seconds=0.5),
            )

            point_map = do_transform_point(point_camera, transform)

            # Apply persistence filter
            if self._is_persistent(point_map):
                pose_map = PoseStamped()
                pose_map.header.frame_id = "map"
                pose_map.header.stamp = self.get_clock().now().to_msg()
                pose_map.pose.position = point_map.point
                pose_map.pose.orientation.w = 1.0

                self.target_pose_pub.publish(pose_map)
                self.get_logger().info(
                    f"Target localized: ({point_map.point.x:.2f}, {point_map.point.y:.2f}, {point_map.point.z:.2f})"
                )

                # Debug visualization
                if self.latest_rgb is not None:
                    debug_img = self.latest_rgb.copy()
                    cv2.circle(debug_img, (center_u, center_v), 10, (0, 255, 0), 2)
                    cv2.putText(
                        debug_img,
                        f"Z:{Z:.2f}m",
                        (center_u, center_v - 15),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.5,
                        (0, 255, 0),
                        2,
                    )
                    debug_msg = self.bridge.cv2_to_imgmsg(debug_img, encoding="bgr8")
                    self.debug_pub.publish(debug_msg)

        except Exception as e:
            self.get_logger().error(f"Transform failed: {e}")

    def _is_persistent(self, point_map):
        """Persistence filter: require stable detection over N frames."""
        self.detection_buffer.append(point_map.point)

        if len(self.detection_buffer) > self.buffer_size:
            self.detection_buffer.pop(0)

        if len(self.detection_buffer) < self.buffer_size:
            return False

        positions = np.array([[p.x, p.y, p.z] for p in self.detection_buffer])
        variance = np.std(positions, axis=0).max()

        return variance < self.spatial_threshold


def main(args=None):
    rclpy.init(args=args)
    node = SemanticLocalizer()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
