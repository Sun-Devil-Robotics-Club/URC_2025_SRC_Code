#!/usr/bin/env python3
import math
import serial
import rclpy
from rclpy.node import Node
from builtin_interfaces.msg import Time
from sensor_msgs.msg import NavSatFix, NavSatStatus
from geometry_msgs.msg import TwistStamped
from rtcm_msgs.msg import Message as RTCMMessage  # sudo apt install ros-humble-rtcm-msgs
from pyubx2 import UBXReader, UBXMessage, GET
from rclpy.time import Time as RosTime


class RTKGNSSNode(Node):
    """
    Minimal u-blox RTK GNSS node:
      - Serial read UBX NAV-PVT
      - Publish /gps/fix (NavSatFix) with realistic covariance
      - Publish /gps/vel (TwistStamped) in ENU (east/north from gSpeed+heading)
      - Subscribe /rtcm and forward RTCM bytes to receiver
    """

    def __init__(self):
        super().__init__("rtk_gnss_node")

        # ---- Parameters ----
        self.declare_parameter("port", "/dev/ttyUSB0")
        self.declare_parameter("baudrate", 921600)
        self.declare_parameter("frame_id", "gps_link")           # frame of antenna
        self.declare_parameter("timeout", 0.25)                   # serial read timeout (s)
        self.declare_parameter("publish_vel", True)               # publish /gps/vel
        self.declare_parameter("rate_hz", 10.0)                   # read rate
        self.declare_parameter("use_hmsl", True)                  # True: altitude = hMSL (MSL), False: height (ellipsoid)
        self.declare_parameter("min_fix_type", 3)                 # 3D fix or better required to publish
        self.declare_parameter("rtcm_write_port", "")             # if different port for RTCM, leave empty to reuse
        self.declare_parameter("log_rtcm_bytes", False)

        port = self.get_parameter("port").value
        baud = int(self.get_parameter("baudrate").value)
        timeout = float(self.get_parameter("timeout").value)
        self.frame_id = self.get_parameter("frame_id").value
        self.publish_vel = bool(self.get_parameter("publish_vel").value)
        self.rate_hz = float(self.get_parameter("rate_hz").value)
        self.use_hmsl = bool(self.get_parameter("use_hmsl").value)
        self.min_fix_type = int(self.get_parameter("min_fix_type").value)
        rtcm_port = self.get_parameter("rtcm_write_port").value or port
        self.log_rtcm = bool(self.get_parameter("log_rtcm_bytes").value)

        # ---- Serial ----
        try:
            self.ser_gnss = serial.Serial(port, baudrate=baud, timeout=timeout)
            self.ubx_reader = UBXReader(self.ser_gnss, protfilter=UBXReader.UBX_ONLY)
            self.get_logger().info(f"Connected GNSS on {port} @ {baud}")
        except Exception as e:
            self.get_logger().fatal(f"Failed to open GNSS port {port}: {e}")
            raise

        # RTCM might go to same port or a 2nd one (e.g., UART2)
        try:
            self.ser_rtcm = (self.ser_gnss if rtcm_port == port
                             else serial.Serial(rtcm_port, baudrate=baud, timeout=timeout))
            if rtcm_port != port:
                self.get_logger().info(f"RTCM corrections will be written to {rtcm_port} @ {baud}")
        except Exception as e:
            self.get_logger().fatal(f"Failed to open RTCM port {rtcm_port}: {e}")
            raise

        # ---- ROS I/O ----
        self.fix_pub = self.create_publisher(NavSatFix, "/gps/fix", 10)
        self.vel_pub = self.create_publisher(TwistStamped, "/gps/vel", 10) if self.publish_vel else None
        self.rtcm_sub = self.create_subscription(RTCMMessage, "/rtcm", self._rtcm_cb, 10)

        # 10 Hz default read loop
        self.timer = self.create_timer(1.0 / self.rate_hz, self._read_once)
        self.get_logger().info("RTK GNSS node started.")

    # ---------- RTCM passthrough ----------
    def _rtcm_cb(self, msg: RTCMMessage):
        try:
            self.ser_rtcm.write(msg.data)
            if self.log_rtcm:
                self.get_logger().info(f"RTCM {len(msg.data)} bytes forwarded")
        except Exception as e:
            self.get_logger().error(f"Failed writing RTCM: {e}")

    # ---------- Read/Publish loop ----------
    def _read_once(self):
        try:
            raw, parsed = self.ubx_reader.read()  # non-blocking with timeout
            if not parsed:
                return

            # We only handle NAV-PVT here; extend if you want INS/HNR/etc.
            if getattr(parsed, "identity", "") == "NAV-PVT":
                # Conditions for valid GNSS
                gnss_ok = bool(getattr(parsed, "gnssFixOK", 0))
                fix_type = int(getattr(parsed, "fixType", 0))  # 0..5
                carr_soln = int(getattr(parsed, "carrSoln", 0))  # 0 none, 1 float, 2 fixed

                if not gnss_ok or fix_type < self.min_fix_type:
                    # Don’t spam; only log occasionally
                    return

                # Lat/Lon in 1e-7 deg, height mm
                lat = float(parsed.lat) * 1e-7
                lon = float(parsed.lon) * 1e-7
                alt_m = (float(parsed.hMSL) if self.use_hmsl else float(parsed.height)) / 1000.0

                # Accuracy (mm) -> stddev (m)
                hacc_m = float(parsed.hAcc) / 1000.0
                vacc_m = float(parsed.vAcc) / 1000.0
                var_e = (hacc_m / math.sqrt(2.0)) ** 2  # split horizontal equally into E/N
                var_n = (hacc_m / math.sqrt(2.0)) ** 2
                var_u = (vacc_m) ** 2

                # Build NavSatFix
                fix = NavSatFix()
                fix.header.stamp = self.get_clock().now().to_msg()
                fix.header.frame_id = self.frame_id
                fix.latitude = lat
                fix.longitude = lon
                fix.altitude = alt_m

                # Status mapping
                # -1 NO_FIX, 0 FIX, 1 SBAS, 2 GBAS (we piggyback: 2=RTK FIX, 1=RTK FLOAT)
                if carr_soln == 2:
                    fix.status.status = NavSatStatus.STATUS_GBAS_FIX
                elif carr_soln == 1:
                    fix.status.status = NavSatStatus.STATUS_SBAS_FIX
                else:
                    fix.status.status = NavSatStatus.STATUS_FIX
                fix.status.service = NavSatStatus.SERVICE_GPS  # add bitwise OR for others if enabled

                fix.position_covariance_type = NavSatFix.COVARIANCE_TYPE_DIAGONAL_KNOWN
                fix.position_covariance = [var_e, 0.0, 0.0,
                                           0.0, var_n, 0.0,
                                           0.0, 0.0, var_u]

                self.fix_pub.publish(fix)

                # Optional: publish ENU velocity (east/north) from gSpeed + heading
                if self.vel_pub:
                    # gSpeed mm/s, headMot 1e-5 deg (fallback to headVeh/headAcc if needed)
                    spd = float(getattr(parsed, "gSpeed", 0.0)) / 1000.0  # m/s
                    head_deg = float(getattr(parsed, "headMot", getattr(parsed, "headVeh", 0.0))) * 1e-5
                    head_rad = math.radians(head_deg)

                    # In ENU: vx = east = speed * sin(heading), vy = north = speed * cos(heading)
                    vx = spd * math.sin(head_rad)
                    vy = spd * math.cos(head_rad)

                    vel = TwistStamped()
                    vel.header.stamp = fix.header.stamp
                    vel.header.frame_id = "earth"  # velocity in ENU world
                    vel.twist.linear.x = vx
                    vel.twist.linear.y = vy
                    vel.twist.linear.z = 0.0
                    self.vel_pub.publish(vel)

        except Exception as e:
            self.get_logger().warn(f"Read loop error: {e}")


def main(args=None):
    rclpy.init(args=args)
    node = RTKGNSSNode()
    try:
        rclpy.spin(node)
    finally:
        rclpy.shutdown()


if __name__ == "__main__":
    main()