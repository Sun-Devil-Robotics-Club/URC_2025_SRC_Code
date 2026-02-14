import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image, CameraInfo
from geometry_msgs.msg import PoseStamped
from cv_bridge import CvBridge
import cv2
import numpy as np
from std_msgs.msg import String

# add near the top
import yaml
import os

class DetectARTag(Node):
    def __init__(self):
        super().__init__("detect_ar_tag")

        # ---- Parameters ----
        self.declare_parameter('use_local_cam', False)
        self.declare_parameter('device_id', 0)
        self.declare_parameter('image_topic', '/camera/image_raw')
        self.declare_parameter('camera_info_topic', '/camera/camera_info')
        self.declare_parameter('cam_yaml', '')  # optional intrinsics file

        use_local = self.get_parameter('use_local_cam').value
        dev_id    = int(self.get_parameter('device_id').value)
        image_topic = self.get_parameter('image_topic').value
        camera_info_topic = self.get_parameter('camera_info_topic').value
        cam_yaml = self.get_parameter('cam_yaml').value

        # ---- Intrinsics ----
        self.camera_matrix = np.array([[500, 0, 320],
                                       [0, 500, 240],
                                       [0,   0,   1]], dtype=float)
        self.dist_coeffs = np.zeros((5,1), dtype=float)
        if cam_yaml and os.path.exists(cam_yaml):
            try:
                with open(cam_yaml, 'r') as f:
                    data = yaml.safe_load(f)
                k = data['camera_matrix']['data']
                d = data['distortion_coefficients']['data']
                self.camera_matrix = np.array(k, dtype=float).reshape(3,3)
                self.dist_coeffs = np.array(d, dtype=float).reshape(-1,1)
                self.get_logger().info(f"Loaded intrinsics from {cam_yaml}")
            except Exception as e:
                self.get_logger().warn(f"Failed to load {cam_yaml}: {e}")

        # ---- Pubs ----
        self.pose_pub = self.create_publisher(PoseStamped, '/detected_ar_tag_pose', 10)
        self.status_pub = self.create_publisher(String, '/ar_tag_status', 10)

        self.bridge = CvBridge()
        self.aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
        self.status = String(); self.status.data = "RUNNING"

        if use_local:
            # Local webcam path (no ROS image subscription)
            self.get_logger().info(f"Using local camera /dev/video{dev_id}")
            self.cap = cv2.VideoCapture(dev_id)
            # optional: set resolution
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            if not self.cap.isOpened():
                self.get_logger().error("Could not open local camera")
            # timer to grab frames
            self.timer = self.create_timer(1.0/30.0, self.timer_cb)
        else:
            # ROS image + camera_info subscriptions (Gazebo / ZED path)
            self.subscription = self.create_subscription(Image, image_topic, self.image_callback, 10)
            self.camera_info_sub = self.create_subscription(CameraInfo, camera_info_topic, self.camera_info_callback, 10)
            self.get_logger().info(f"Subscribing to {image_topic} and {camera_info_topic}")

    def camera_info_callback(self, msg):
        self.camera_matrix = np.array(msg.k).reshape(3, 3)
        self.dist_coeffs = np.array(msg.d).reshape(-1,1)
        self.get_logger().info("Camera calibration updated from CameraInfo")

    def process_frame(self, cv_image, frame_id="camera_link"):
        corners, ids, _ = cv2.aruco.detectMarkers(cv_image, self.aruco_dict)
        display_image = cv_image
        if ids is not None:
            rvecs, tvecs, _ = cv2.aruco.estimatePoseSingleMarkers(corners, 0.05, self.camera_matrix, self.dist_coeffs)
            for i, id in enumerate(ids):
                pose = PoseStamped()
                pose.header.frame_id = frame_id
                pose.header.stamp = self.get_clock().now().to_msg()
                pose.pose.position.x = float(tvecs[i][0][0])
                pose.pose.position.y = float(tvecs[i][0][1])
                pose.pose.position.z = float(tvecs[i][0][2])
                pose.pose.orientation.w = 1.0
                self.pose_pub.publish(pose)
                self.status.data = f"SUCCESS: ID {int(id[0])}"
                self.status_pub.publish(self.status)
            cv2.aruco.drawDetectedMarkers(display_image, corners, ids)
        else:
            self.status.data = "RUNNING"
            self.status_pub.publish(self.status)

        cv2.imshow("AR Tag Detection", display_image)
        cv2.waitKey(1)

    def image_callback(self, msg):
        cv_image = self.bridge.imgmsg_to_cv2(msg, "bgr8")
        self.process_frame(cv_image, frame_id="camera_link")

    def timer_cb(self):
        ok, frame = self.cap.read()
        if not ok:
            return
        self.process_frame(frame, frame_id="webcam_link")

    def destroy_node(self):
        try:
            if hasattr(self, 'cap') and self.cap and self.cap.isOpened():
                self.cap.release()
        except:
            pass
        cv2.destroyAllWindows()
        super().destroy_node()

def main(args=None):
    rclpy.init(args=args)
    node = DetectARTag()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()
if __name__ == "__main__":
    main()
