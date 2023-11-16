import rclpy
from rclpy.node import Node
# Import the hypothetical custom service definition for setting an LED color
from sdrc_interfaces.srv import SetLed

class LedServerNode(Node):
    def __init__(self):
        super().__init__(node_name="led_server")
        self.server_ = self.create_service(SetLed, "set_led", self.set_led_callback)
        self.get_logger().info("LED Server Created")
    
    def set_led_callback(self, request, response):
        self.get_logger().info(f"The LED color is set to: {request.color}")
        response.success = True
        return response 

def main(args=None):
    rclpy.init(args=args)
    node = LedServerNode()
    rclpy.spin(node)
    rclpy.shutdown()

if __name__ == "__main__":
    main()