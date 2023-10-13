import os
import sys
import time
from cmath import pi
from logging import exception

import odrive
from odrive.utils import dump_errors


def countdown(t):
    for i in range(t):
        if (t - i) > 1:
            print(f"Please wait {t - i} seconds  \t", end="\r")
        else:
            print("Please wait 1 second  \t", end="\r")
        time.sleep(1)
    print("                          ", end="\r")


def save_odrive(odrv, odrv_ID):
    print("Saving ODrive")

    odrv.axis0.requested_state = 1
    odrv.axis1.requested_state = 1
    try:
        odrv.save_configuration()
        countdown(5)
    except Exception:
        countdown(5)
    print()

    odrv = odrive.find_any(serial_number=odrv_ID)
    odrv.axis0.requested_state = 1
    odrv.axis1.requested_state = 1

    return odrv


def autocal_stepper(odrv, odrv_ID):
    # Continue/cancel autodetection
    # str_in = input(
    #     "Move stepper motor into safe area\nPress ENTER to continue or X to cancel\n"
    # )

    # if str_in in ["x", "X"]:
    #     print()
    #     return

    odrv.config.dc_max_positive_current = 15
    odrv.config.enable_brake_resistor = True

    odrv.axis1.motor.config.pole_pairs = 15
    odrv.axis1.motor.config.resistance_calib_max_voltage = 2
    odrv.axis1.motor.config.motor_type = 0  # "MOTOR_TYPE_HIGH_CURRENT"
    odrv.axis1.motor.config.current_lim = 15
    odrv.axis1.motor.config.requested_current_range = 15
    odrv.axis1.controller.config.vel_limit = 5000

    odrv.axis1.encoder.config.cpr = 4096
    odrv.axis1.motor.config.torque_constant = 8.7 # / 12.5
    odrv.axis1.encoder.config.bandwidth = 3000
    odrv.axis1.config.calibration_lockin.current = 5
    odrv.axis1.config.calibration_lockin.ramp_distance = 3.1415
    odrv.axis1.config.calibration_lockin.accel = 20
    odrv.axis1.config.calibration_lockin.vel = 40
    odrv.axis1.controller.config.pos_gain = 10.0 # Overshoot; increase for less
    odrv.axis1.controller.config.vel_gain = 18.0 # Vibration Descress for less
    odrv.axis0.controller.config.vel_integrator_gain = 0.5 * 0.33 * odrv.axis1.controller.config.vel_gain 
    odrv.axis1.controller.config.input_mode = 2 # Control MOde Velocity
    # odrv.axis1.controller.config.input_mode = 5  # "INPUT_MODE_TRAP_TRAJ"
    # odrv.axis1.trap_traj.config.vel_limit = 2
    # odrv.axis1.trap_traj.config.accel_limit = 2
    # odrv.axis1.trap_traj.config.decel_limit = 2
    odrv = save_odrive(odrv, odrv_ID)

    # print("Calibrating Stepper Motor")
    # # odrv.axis1.requested_state = 4 # AXIS_STATE_MOTOR_CALIBRATION
    # odrv.axis1.requested_state = 3  # AXIS_STATE_FULL_CALIBRATION_SEQUENCE
    # countdown(20)


    print()

    dump_errors(odrv)

    # Error exit case
    if odrv.axis1.error:
        print("ERROR")
        sys.exit()

    # Save ODrive
    # odrv = save_odrive(odrv, odrv_ID)

    odrv.clear_errors()
    odrv.axis1.requested_state = 4 # AXIS_STATE_MOTOR_CALIBRATION
    countdown(10)
    odrv.axis1.motor.config.pre_calibrated = True
    odrv.axis1.requested_state = 7 # AXIS_STATE_ENCODER_OFFSET_CALIBRATION
    countdown(15)
    odrv.axis1.requested_state = 8 # AXIS_STATE_CLOSED_LOOP_CONTROL
    countdown(5)
    odrv.axis1.controller.input_vel = 20
    countdown(20)

    odrv = save_odrive(odrv, odrv_ID)

    dump_errors(odrv)

    return odrv


def print_odrive_info(odrv, odrv_ID):
    print(
        f"ODrive {odrv_ID} with hardware v{odrv.hw_version_major}.{odrv.hw_version_minor}-{odrv.hw_version_variant}V running firmware v{odrv.fw_version_major}.{odrv.fw_version_minor}.{odrv.fw_version_revision}.{odrv.fw_version_unreleased}"
    )
    print(f"Pulling {odrv.ibus}A at {odrv.vbus_voltage}V\n")


def autocal(odrv, odrv_ID):
    print("Running Variable Stiffness Treadmill Autocalibrater v001")
    print_odrive_info(odrv, odrv_ID)

    str_in = input("Press ENTER to clear errors or E to erase configuration\n")

    if str_in in ["e", "E"]:
        odrv.clear_errors()
        print()
        print("Erasing ODrive")
        try:
            odrv.erase_configuration()
            countdown(5)
        except Exception:
            countdown(5)
        odrv = odrive.find_any(serial_number=odrv_ID)
        # odrv.clear_errors()
        print()
    else:
        odrv.clear_errors()

    odrv = save_odrive(odrv, odrv_ID)

    # str_in = input("Press ENTER to skip or Y to start stepper motor autocalibration\n")

    # if str_in in ["y", "Y"]:
    #     print()
    #     odrv = autocal_stepper(odrv, odrv_ID)

    odrv = autocal_stepper(odrv, odrv_ID)

    return odrv


def main():
    print("starting autocalibration sequence")

    # odrv_ID = "206934915748"
    odrv0_ID = "207D349B5748"

    print("Searching For Odrives")
    odrv0 = odrive.find_any(serial_number=odrv0_ID)

    print("Found Odrive begginnig auto calibration sequence")
    odrv0 = autocal(odrv0, odrv0_ID)


if __name__ == "__main__":
    main()
