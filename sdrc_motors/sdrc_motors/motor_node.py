import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from .arduino import Arduino


class MotorNode(Node):
    # TODO: Add rate limiting to make sure arduino doesn't get spammed with commadn velocities that are very similair
    # TODO: Add maximum velocites to the angular and linear velocities
    def __init__(self):
        super().__init__("motor_node")
        self.declare_parameter("serial_port", "/dev/ttyUSB0")
        self.declare_parameter("baud_rate", 9600)
        self.declare_parameter("wheel_seperation_m", 0.5)

        self.serial_port = (
            self.get_parameter("serial_port").get_parameter_value().string_value
        )
        self.baudrate = (
            self.get_parameter("baud_rate").get_parameter_value().integer_value
        )
        self.wheel_separation_m = (
            self.get_parameter("wheel_seperation_m").get_parameter_value().double_value
        )

        self.subscription = self.create_subscription(
            Twist, "cmd_vel", self.cmd_vel_callback, 10
        )

        self.get_logger().info("Motor Node is started and subscribed to cmd_vel")

    def cmd_vel_callback(self, msg: Twist):
        V_left_m_per_s, V_right_m_per_s = self.calculate_motor_velocities(
            msg.linear.x, msg.angular.z, self.wheel_separation_m
        )

        self.get_logger().info(
            f"Received cmd_vel: linear={msg.linear}, angular={msg.angular}, velocity_left={V_left_m_per_s}, velocity_right={V_right_m_per_s}"
        )

        err = self.send_velocity_msg(V_left_m_per_s, V_right_m_per_s)
        if err:
            self.get_logger().info(f"failed to send message to arduino: {err}")

    def calculate_motor_velocities(
        self,
        linear_vel_m_per_s: float,
        angular_vel_rad_per_s: float,
        wheel_separation_m: float,
    ) -> tuple:
        V_left_m_per_s = linear_vel_m_per_s - (
            angular_vel_rad_per_s * wheel_separation_m / 2
        )
        V_right_m_per_s = linear_vel_m_per_s + (
            angular_vel_rad_per_s * wheel_separation_m / 2
        )

        return V_left_m_per_s, V_right_m_per_s

    def send_velocity_msg(self, V_left_m_per_s, V_right_m_per_s):
        with Arduino(self.serial_port, self.baudrate) as arduino:
            err = arduino.send_message(f"m {V_left_m_per_s} {V_right_m_per_s}")

        return err


def main(args=None):
    rclpy.init(args=args)
    node = MotorNode()
    rclpy.spin(node)
    rclpy.shutdown()


if __name__ == "__main__":
    main()
