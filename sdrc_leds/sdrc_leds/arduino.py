import serial

class Arduino():
    def __init__(self, arduino_port, arduino_baudrate):
        print(f"Initializing Arduino Communications to {arduino_port} baudrate: {arduino_baudrate}")
        self.serial = serial.Serial(port=arduino_port, baudrate=arduino_baudrate)
        self.serial.flush()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def send_message(self, message: str):
        try:
            self.serial.write(message.encode()) 
            self.serial.flush()
            return None  
        except serial.SerialException as e:
            print(f"SerialException: {e}")
            return f"SerialException: {e}"
        except serial.SerialTimeoutException as e:
            print(f"SerialTimeoutException: {e}")
            return f"SerialTimeoutException: {e}"
        except Exception as e: 
            print(f"Exception: {e}")
            return f"Exception: {e}"

    def close(self):
        print("Closing serial connection")
        try:
            self.serial.close()
        except Exception as e:
            print(f"Error closing serial connection: {e}")
