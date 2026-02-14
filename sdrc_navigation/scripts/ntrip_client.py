#!/usr/bin/env python3
import os, socket, base64, rclpy, time
from rclpy.node import Node
from rtcm_msgs.msg import Message as RTCMMessage
from sensor_msgs.msg import NavSatFix

class NTRIPClient(Node):
    def __init__(self):
        super().__init__("ntrip_client")
        self.declare_parameter("host", "caster.example.com")
        self.declare_parameter("port", 2101)
        self.declare_parameter("mount", "MOUNTPOINT")
        self.declare_parameter("user", "")
        self.declare_parameter("password", "")
        self.declare_parameter("send_gga", True)
        self.declare_parameter("gga_period", 15.0)

        self.pub = self.create_publisher(RTCMMessage, "/rtcm", 10)
        self.sock = None
        self.last_gga = 0.0
        self.latest_fix = None
        self.sub_fix = self.create_subscription(NavSatFix, "/gps/fix", self._fix_cb, 10)
        self.timer = self.create_timer(0.1, self._tick)

    def _fix_cb(self, msg: NavSatFix):
        self.latest_fix = msg

    def _connect(self):
        host = self.get_parameter("host").value
        port = int(self.get_parameter("port").value)
        mount = self.get_parameter("mount").value
        user = self.get_parameter("user").value
        pw = self.get_parameter("password").value
        auth = base64.b64encode(f"{user}:{pw}".encode()).decode() if user else ""
        req = (f"GET /{mount} HTTP/1.0\r\nHost: {host}\r\nNtrip-Version: Ntrip/2.0\r\n"
               f"User-Agent: sdrc-ntrip\r\n" + (f"Authorization: Basic {auth}\r\n" if auth else "") + "\r\n")
        self.sock = socket.create_connection((host, port), timeout=10)
        self.sock.sendall(req.encode())
        hdr = self.sock.recv(1024)
        if b"200 OK" not in hdr:
            raise RuntimeError(f"NTRIP not OK: {hdr!r}")
        self.get_logger().info("NTRIP connected")

    def _maybe_send_gga(self):
        if not self.get_parameter("send_gga").value or self.latest_fix is None:
            return
        now = time.time()
        if now - self.last_gga < float(self.get_parameter("gga_period").value):
            return
        lat = self.latest_fix.latitude
        lon = self.latest_fix.longitude
        alt = self.latest_fix.altitude
        # Minimal GGA
        def dm(x, is_lat):
            d = int(abs(x))
            m = (abs(x) - d) * 60.0
            return f"{d:02d}{m:07.4f}" if is_lat else f"{d:03d}{m:07.4f}"
        latc = "N" if lat >= 0 else "S"
        lonc = "E" if lon >= 0 else "W"
        gga = f"$GPGGA,000000,{dm(lat,True)},{latc},{dm(lon,False)},{lonc},1,12,1.0,{alt:.1f},M,0.0,M,,*00\r\n"
        try:
            self.sock.sendall(gga.encode())
            self.last_gga = now
        except Exception as e:
            self.get_logger().warn(f"GGA send failed: {e}")

    def _tick(self):
        try:
            if self.sock is None:
                self._connect()
                return
            self._maybe_send_gga()
            data = self.sock.recv(4096)
            if data:
                self.pub.publish(RTCMMessage(data=data))
        except Exception as e:
            self.get_logger().warn(f"NTRIP reconnecting: {e}")
            try:
                if self.sock: self.sock.close()
            except Exception:
                pass
            self.sock = None

def main():
    rclpy.init()
    node = NTRIPClient()
    rclpy.spin(node)
    rclpy.shutdown()

if __name__ == "__main__":