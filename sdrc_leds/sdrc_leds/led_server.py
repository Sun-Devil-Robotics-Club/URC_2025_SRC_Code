import rclpy
from rclpy.node import Node
# Import the hypothetical custom service definition for setting an LED color
from sdrc_interfaces.srv import SetLed
from enum import Enum
import serial
from arduino import Arduino

# Maps Colors To Corresponding Arduino Message/Command
ledColorCommands = { 
    "blue": 0, 
    "red": 1,
    "green": 2,
}

class LedServerNode(Node):
    def __init__(self):
        super().__init__(node_name="led_server")

        self.declare_parameter('serial_port', '/dev/ttyUSB0')
        self.declare_parameter('baud_rate', 9600)

        self.serial_port = self.get_parameter('serial_port').get_parameter_value().string_value
        self.baud_rate = self.get_parameter('baud_rate').get_parameter_value().integer_value

        self.logger = self.get_logger()
        self.server_ = self.create_service(SetLed, "set_led", self.set_led_callback)
        self.logger.info("LED Server Created")
    
    def set_led_callback(self, request, response):
        self.logger.info(f"Recieved message to set color to {request.color}")

        if request.color not in ledColorCommands:
            self.logger.error(f"Arduino doesn't support recieved color")
            response.success = False
            return response

        with Arduino(port, baudrate) as arduino:      
            err = arduino.send_message(str(ledColorCommands[request.color]))
            
            if err is not None:
                self.logger.error(f"Failed to set color {err}")
                response.success = False
                return response
            
        self.logger.info(f"{request.color} successfully set")
        response.success = True 
        return response

def main(args=None):
    rclpy.init(args=args)
    node = LedServerNode()
    rclpy.spin(node)
    rclpy.shutdown()

if __name__ == "__main__":
    main()