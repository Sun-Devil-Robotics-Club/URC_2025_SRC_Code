import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from std_msgs.msg import String
from cv_bridge import CvBridge
import cv2
import base64


class DecoderNode(Node):
    def __init__(self):
        super().__init__("decoder_node")
        self.subscription = self.create_subscription(
            Image, "/camera/image_raw", self.listener_callback, 10
        )
        self.publisher = self.create_publisher(String, "/camera/image_base64", 10)
        self.bridge = CvBridge()
        self.get_logger().info("Decoder node is started")

    def listener_callback(self, data):
        try:
            cv_image = self.bridge.imgmsg_to_cv2(data, "bgr8")

            ret, jpeg_image = cv2.imencode(".jpg", cv_image)
            if not ret:
                raise RuntimeError("Failed to encode image to JPEG format")

            base64_str = base64.b64encode(jpeg_image).decode("utf-8")
            self.publisher.publish(String(data=base64_str))

        except Exception as e:
            self.get_logger().error("Failed to decode image: %s" % str(e))


def main(args=None):
    rclpy.init(args=args)
    decoder_node = DecoderNode()
    rclpy.spin(decoder_node)
    decoder_node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
