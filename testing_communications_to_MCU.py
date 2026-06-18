import serial
import time

PORT = "/dev/tty.usbmodem112301"  # change this
BAUDRATE = 9600

ser = serial.Serial(PORT, BAUDRATE, timeout=1)

time.sleep(2)

print("Laptop UART sender started.")
print("Type commands such as:")
print("READ10")
print("READALL")
print("READLINE")
print("READINTO")
print("WRITE")
print()

while True:
    message = input("Send to MCU: ")

    # Add newline so MCU's uart.readline() knows where the command ends
    ser.write((message + "\n").encode("utf-8"))

    # After WRITE command, try to read response from MCU UART TX
    time.sleep(0.2)

    while ser.in_waiting:
        data = ser.readline()
        print("Received from MCU:", data)

        try:
            print("As text:", data.decode("utf-8").strip())
        except UnicodeDecodeError:
            print("Could not decode as UTF-8")