
# possibly consider implementing: 
display.set_text(
                "t_status",
                "Factor: {:.1f}".format(scale.user_defined_scale_factor)
            )

# ----# ----# ----# ----# ----# ----# ----# ----# ----# ----# ----# ----# ----


def get_command():
    line = uart.readline()
    if line:
        line = line.strip()   # removes \r and \n
        print(line)
    return line # returns a byte object b"string", neither decoded or split

byte_data_1 = b"TARE" # T 0D 0A
byte_data_2 = b"CAL:\x05\x00\r\n" # CAL:123 0D 0A
print(byte_data_2)
print(byte_data_2.decode())
print(len(byte_data_2.decode()))
print(byte_data_2[4:6])
print(int.from_bytes(byte_data_2[4:6], byteorder='little'))
# result_big = int.from_bytes(b'\x00\x10', byteorder='little')

# Decode to string and split into a list
result_1 = byte_data_1.decode('utf-8') # returns a string
result_2 = byte_data_2.decode('utf-8').split(":") # returns a list of strings

# # print(result_1)
# # print(result_2)
# # print(len(result_1))
# # print(len(result_2))
# # print(type(result))
# print(byte_data_2)
# print(type(byte_data_2)) # byte object
# print(byte_data_2[4:5])
# print(type(byte_data_2[4:6]))

command = display.get_command()
if command == b"TARE":
    # tare
    scale.set_offset()
elif len(command.decode().split(":")) == 2 and command.decode().split(":")[0] == "CAL":
    # calibrate
    calibration_weight = int.from_bytes(byte_data_2[4:6], byteorder='little')