from machine import UART, Pin
from time import sleep_ms

uart = UART(
    1,
    baudrate=9600,
    bits=8,
    parity=None,
    stop=1,
    rx=Pin(18),   # MCU RX pin: receives data from laptop TX
    tx=Pin(17)    # MCU TX pin: sends data to laptop RX
)

print("UART function test started.")
print("Send commands from laptop:")
print("READ10")
print("READALL")
print("READLINE")
print("READINTO")
print("WRITE")
print("------------------------")


def print_bytes(label, data):
    print(label)

    if data is None:
        print("Result: None")
        print("------------------------")
        return

    print("Raw bytes:", data)
    print("Decimal list:", list(data))
    print("Hex:", data.hex())

    try:
        print("Text:", data.decode("utf-8"))
    except UnicodeError:
        print("Text: could not decode as UTF-8")

    print("------------------------")


while True:
    if uart.any():
        print("uart.any():", uart.any(), "byte(s) waiting")

        # Read one full line from laptop.
        # This means the laptop should send something ending with \n.
        command = uart.readline()

        print_bytes("Command received using uart.readline():", command)

        if command is None:
            continue

        command_text = command.decode("utf-8").strip()

        if command_text == "READ10":
            print("Testing uart.read(10)")
            print("Now send at least 10 characters from laptop.")
            sleep_ms(3000)

            data = uart.read(10)
            print_bytes("Result of uart.read(10):", data)

        elif command_text == "READALL":
            print("Testing uart.read()")
            print("Now send some characters from laptop.")
            sleep_ms(3000)

            data = uart.read()
            print_bytes("Result of uart.read():", data)

        elif command_text == "READLINE":
            print("Testing uart.readline()")
            print("Now send a line ending with newline.")
            sleep_ms(3000)

            data = uart.readline()
            print_bytes("Result of uart.readline():", data)

        elif command_text == "READINTO":
            print("Testing uart.readinto(buf)")
            print("Now send some characters from laptop.")
            sleep_ms(3000)

            buf = bytearray(10)
            num_bytes = uart.readinto(buf)

            print("Result of uart.readinto(buf):")
            print("Number of bytes read:", num_bytes)
            print("Whole buffer:", buf)
            print("Whole buffer decimal:", list(buf))
            print("Whole buffer hex:", buf.hex())

            if num_bytes is not None:
                actual_data = buf[:num_bytes]
                print("Actual data read:", actual_data)
                print("Actual data text:", actual_data.decode("utf-8"))

            print("------------------------")

        elif command_text == "WRITE":
            print("Testing uart.write('abc')")
            bytes_written = uart.write("abc\n")

            print("uart.write returned:", bytes_written)
            print("This means the MCU wrote", bytes_written, "byte(s) to UART.")
            print("------------------------")

        else:
            print("Unknown command:", command_text)
            print("------------------------")

    sleep_ms(50)