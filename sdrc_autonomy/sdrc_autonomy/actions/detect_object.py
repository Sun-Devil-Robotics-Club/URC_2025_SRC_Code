import os
from pathlib import Path
import cv2
import numpy as np
import rclpy
from rclpy.node import Node
from cv_bridge import CvBridge
from sensor_msgs.msg import Image, RegionOfInterest
from geometry_msgs.msg import PointStamped
from std_msgs.msg import String

# Optional – only if YOLO is enabled
try:
    import onnxruntime
except ImportError:
    onnxruntime = None


class DetectObject(Node):
    """
    Detects specified objects using a single, unified YOLO-ONNX model with proper
    post-processing including Non-Max Suppression (NMS).
    """
    def __init__(self):
        super().__init__("detect_object")

        # --- Parameters ---
        self.declare_parameter("debug_view", True)
        self.declare_parameter("use_yolo", True)
        # Path to your NEW retrained ONNX model
        self.declare_parameter("yolo_model_path", str(Path("~/Downloads/best.onnx").expanduser()))

        # Detection thresholds - can be tuned in rqt_reconfigure or a launch file
        self.declare_parameter("conf_threshold", 0.5)
        self.declare_parameter("nms_threshold", 0.4)

        # --- Class Members ---
        self.bridge = CvBridge()
        # IMPORTANT: Verify this dictionary matches your training class order
        self.class_labels = {0: "water_bottle", 1: "hammer", 2: "mallet"}

        # Publishers
        self.pub_pt = self.create_publisher(PointStamped, "/detected_objects/points", 10)
        self.pub_roi = self.create_publisher(RegionOfInterest, "/detected_objects/roi", 10)
        self.status_pub = self.create_publisher(String, "/detect_object/status", 10)

        # Subscriber
        self.image_sub = self.create_subscription(
            Image, "/camera/image_raw", self.image_callback, 10
        )

        # --- Initialize YOLO ---
        self.debug_view = self.get_parameter("debug_view").value
        self.session = self._initialize_yolo()

        if self.debug_view:
            cv2.namedWindow("Detection Debug", cv2.WINDOW_AUTOSIZE)
            self.get_logger().info("Debug view enabled.")

        self.get_logger().info("DetectObject node initialized.")

    def _initialize_yolo(self):
        """Initializes the single YOLO ONNX runtime session."""
        if not self.get_parameter("use_yolo").value:
            self.get_logger().info("YOLO is disabled.")
            return None

        if onnxruntime is None:
            self.get_logger().warning("YOLO requested but 'onnxruntime' is not installed.")
            return None

        model_path_str = self.get_parameter("yolo_model_path").value
        if not model_path_str or not Path(model_path_str).exists():
            self.get_logger().error(f"YOLO model not found at '{model_path_str}'.")
            return None

        try:
            session = onnxruntime.InferenceSession(model_path_str, providers=["CPUExecutionProvider"])
            self.get_logger().info(f"Successfully loaded YOLO model from: {model_path_str}")
            return session
        except Exception as e:
            self.get_logger().error(f"Failed to load YOLO model: {e}")
            return None

    def image_callback(self, msg: Image):
        """Main callback to process incoming images."""
        try:
            cv_img = self.bridge.imgmsg_to_cv2(msg, desired_encoding="bgr8")
        except Exception as e:
            self.get_logger().error(f"Failed to convert image: {e}")
            return

        detections = {}
        if self.session:
            detections = self._detect_with_yolo(cv_img)

        if detections:
            self.status_pub.publish(String(data="SUCCESS"))
            for label, (bbox, score) in detections.items():
                self._publish_detection(bbox, label, score, msg.header)
            if self.debug_view:
                self._draw_detections(cv_img, detections)
        else:
            self.status_pub.publish(String(data="FAILURE"))

        if self.debug_view:
            cv2.imshow("Detection Debug", cv_img)
            cv2.waitKey(1)

    def _detect_with_yolo(self, img):
        """Performs object detection using the unified YOLO model."""
        img_height, img_width = img.shape[:2]

        # Pre-process image for YOLO
        input_img = cv2.resize(img, (640, 640))
        input_img = input_img[:, :, ::-1].transpose(2, 0, 1).astype(np.float32) / 255.0
        input_img = np.expand_dims(input_img, axis=0)

        # Get detection thresholds from parameters for real-time tuning
        conf_threshold = self.get_parameter("conf_threshold").value
        nms_threshold = self.get_parameter("nms_threshold").value

        # Run inference
        try:
            outputs = self.session.run(None, {self.session.get_inputs()[0].name: input_img})[0]
        except Exception as e:
            self.get_logger().error(f"YOLO inference failed: {e}")
            return {}

        # Post-process results
        boxes, scores, class_ids = [], [], []
        # Transpose output from [1, N, 8400] to [1, 8400, N] where N = 4 (box) + num_classes
        outputs = outputs.transpose(0, 2, 1)

        for det in outputs[0]:
            confidence = np.max(det[4:])
            if confidence >= conf_threshold:
                class_id = np.argmax(det[4:])
                cx, cy, w, h = det[:4]
                boxes.append([cx, cy, w, h])
                scores.append(confidence)
                class_ids.append(class_id)

        # Apply Non-Max Suppression
        indices = cv2.dnn.NMSBoxes(boxes, np.array(scores), conf_threshold, nms_threshold)

        detections = {}
        for i in indices:
            box = boxes[i]
            class_id = class_ids[i]
            score = scores[i]
            label = self.class_labels.get(class_id, "unknown")

            # Rescale box to original image dimensions
            cx, cy, w, h = box
            x = int((cx - w / 2) * img_width / 640)
            y = int((cy - h / 2) * img_height / 640)
            w = int(w * img_width / 640)
            h = int(h * img_height / 640)

            x = max(0, x)
            y = max(0, y)
            w = min(w, img_width - x)
            h = min(h, img_height - y)
            # --- END OF FIX ---
            # Store detection with its score
            if w > 0 and h > 0:
                detections[label] = ((x, y, w, h), score)

        return detections

    def _publish_detection(self, bbox, label, score, header):
        x, y, w, h = bbox
        pt_msg = PointStamped()
        pt_msg.header = header
        pt_msg.header.frame_id = label # Use frame_id to carry the label
        pt_msg.point.x = float(x + w / 2)
        pt_msg.point.y = float(y + h / 2)
        self.pub_pt.publish(pt_msg)

        roi_msg = RegionOfInterest(x_offset=x, y_offset=y, width=w, height=h)
        self.pub_roi.publish(roi_msg)
        self.get_logger().info(f"Detected '{label}' with confidence {score:.2f}")

    def _draw_detections(self, image, detections):
        for label, (bbox, score) in detections.items():
            x, y, w, h = bbox
            display_text = f"{label}: {score:.2f}"
            cv2.rectangle(image, (x, y), (x + w, y + h), (0, 255, 0), 2)
            cv2.putText(image, display_text, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)


def main(args=None):
    rclpy.init(args=args)
    node = DetectObject()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        if node.debug_view:
            cv2.destroyAllWindows()
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()