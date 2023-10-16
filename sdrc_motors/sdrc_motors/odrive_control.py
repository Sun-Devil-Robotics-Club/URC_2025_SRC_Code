import rclpy
import os 
import sys 
import sys
import os
sys.path.append(os.path.dirname(os.path.realpath(__file__)))
from rclpy.node import Node
from geometry_msgs.msg import Twist
import odrive
from motor_calibration_script import find_odrive, autocal

class OdriveControlNode(Node):
    def __init__(self) -> None: 
        super().__init__("odrive_control_node")
        self.odrv0_ID = "207D349B5748"
        self.get_logger().info("Created Odrive Control Node")

        self.calibrate_odrive(self.odrv0_ID)
        self.subscriber_ = self.create_subscription(Twist, "cmd_vel", self.motor_control_cb, 10)
    
    def calibrate_odrive(self, odrv0_ID: str):
        self.odrv0 = find_odrive(odrv0_ID)
        self.odrv0 = autocal(self.odrv0, odrv0_ID)

    def motor_control_cb(self, msg: Twist) -> None: 
        self.get_logger().info(str(msg.linear.x))
        self.send_motor_command(msg.linear.x)
    
    def send_motor_command(self, linear_velocity: float):
        self.odrv0.axis1.controller.input_vel = linear_velocity
        
    

def main() -> None:
    rclpy.init()
    node = OdriveControlNode()
    rclpy.spin(node)
    rclpy.shutdown()