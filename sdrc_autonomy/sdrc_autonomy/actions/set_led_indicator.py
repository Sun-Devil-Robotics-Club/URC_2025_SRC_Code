import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from sdrc_interfaces.srv import SetLed  # your custom service
from rclpy.timer import Timer

class SetLEDIndicator(Node):
    """
    Subscribes to /rover_state (String: 'AUTONOMOUS'|'TELEOP'|'SUCCESS')
    and calls /set_led (sdrc_interfaces/SetLed) with:
      AUTONOMOUS -> 'red'
      TELEOP     -> 'blue'
      SUCCESS    -> flashing green (toggle green/off @ 2 Hz)
    """
    def __init__(self):
        super().__init__('set_led_indicator')
        self._state_sub = self.create_subscription(String, '/rover_state', self._state_cb, 10)
        self._led_cli = self.create_client(SetLed, 'set_led')
        self._flash_timer: Timer | None = None
        self._flash_on = False

        self.get_logger().info("LED Indicator ready (listening on /rover_state)")

    def _state_cb(self, msg: String):
        state = msg.data.strip().upper()
        if state == 'SUCCESS':
            # start flashing green
            self._stop_flash()
            self._flash_timer = self.create_timer(0.5, self._flash_step)  # 2 Hz
            return
        # not success -> solid color, stop flashing
        self._stop_flash()
        color = 'red' if state == 'AUTONOMOUS' else 'blue'
        self._set_led(color)

    def _flash_step(self):
        self._flash_on = not self._flash_on
        self._set_led('green' if self._flash_on else 'off')

    def _stop_flash(self):
        if self._flash_timer:
            self._flash_timer.cancel()
            self._flash_timer = None
            self._flash_on = False

    def _set_led(self, color: str):
        if not self._led_cli.service_is_ready():
            self.get_logger().warn("set_led service not ready")
            return
        req = SetLed.Request()
        req.color = color
        self._led_cli.call_async(req)

def main(args=None):
    rclpy.init(args=args)
    n = SetLEDIndicator()
    rclpy.spin(n)
    n.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
