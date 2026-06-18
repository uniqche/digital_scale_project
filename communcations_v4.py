# with edits to for waiting page mechanism 
# editing end time: 1:52am June 17th, 2026
# past version

from machine import Pin, UART
from time import sleep_us, sleep_ms


class HX711:
    def __init__(self, dout_pin, sck_pin, gain=128):
        self.dout = Pin(dout_pin, Pin.IN)
        self.sck = Pin(sck_pin, Pin.OUT)
        self.sck.value(0)
        self.offset = 0
        self.temp_cal_weight = 1
        self.temp_scale_factor = 1 
        self.fixed_scale_factor_for_perm_weight_estimation = 1414.8 # do NOT change
        self.perm_scale_factors = [1415.1, 1415.0, 1414.9, 1414.8, 1414.7, 1414.6, 1414.5] # range = 7; holds scale factors for 100, 500, 1000, 1500, 2000, 2500, and 3000 (in order)
        self.perm_calibration_weights = [100, 500, 1000, 1500, 2000, 2500, 3000]
        self.gain = gain
        if gain == 128:
            self.gain_pulses = 1   # Channel A, gain 128
        elif gain == 64:
            self.gain_pulses = 3   # Channel A, gain 64
        elif gain == 32:
            self.gain_pulses = 2   # Channel B, gain 32
        else:
            raise ValueError("Gain must be 128, 64, or 32")
    def is_ready(self): # in python, you do not have to define the return type of a function
        return self.dout.value() == 0 # boolean
    def read(self):
        # Wait until HX711 is ready
        while not self.is_ready():
            pass
        value = 0
        # Read 24 bits
        for _ in range(24):
            self.sck.value(1)
            sleep_us(1)
            value = value << 1
            if self.dout.value(): # if self.dout = 1, then value += 1. else, nothing happens. 
                value += 1
            self.sck.value(0)
            sleep_us(1)
        # Set gain for next reading
        for _ in range(self.gain_pulses):
            self.sck.value(1)
            sleep_us(1)
            self.sck.value(0)
            sleep_us(1)
        # Convert from unsigned 24-bit to signed 24-bit
        if value & 0x800000: # applies a mask of 10000000 00000000 00000000 to value's 24-bit number, so that if value's leftmost number = 1, the conditional = true
            value -= 0x1000000 # changes to signed number
        return value
    def set_offset(self, offset_samples = 10):
        print("Taring starting...")
        sleep_ms(500)
        total = 0
        for i in range(offset_samples):
            reading = self.read()
            sleep_us(10)
            total += reading
            # print("Offset reading {}: {}".format(i + 1, reading))
        offset_average = total // offset_samples
        self.offset = offset_average
        print()
        print("Taring finished.")
        # print("Average offset calculated = {}".format(offset_average))
        print("Newly stored offset = {}".format(self.offset))
    def set_temp_scale_factor(self, temp_cal_weight):
        self.temp_cal_weight = temp_cal_weight
        print("Waiting 3 seconds for calibration weight's measurements to settle to a steady measurement")
        sleep_ms(3000)
        print("Sampling ADC values right now")
        readings = []
        for i in range(11):
            reading = self.read()
            readings.append(reading)
            print("Calibration weight reading {}: {}".format(i + 1, reading))
            sleep_ms(10)
        readings.sort()
        middle_index = 11 // 2
        adc_median = readings[middle_index]
        print("Median filtered ADC value for calibration weight is", adc_median)
        print("Offset is", self.offset)
        print("Given calibration weight is", temp_cal_weight)
        # print("Previous scale factor:", self.temp_scale_factor)
# ***********************
        untruncated_scale_factor = (adc_median - self.offset) / temp_cal_weight
        truncated_scale_factor = int(untruncated_scale_factor * 10) / 10
        self.temp_scale_factor = truncated_scale_factor
# ***********************
        print("Untruncated scale factor:", untruncated_scale_factor)
        print("Truncated and stored scale factor:", self.temp_scale_factor)
        # print("Calibration complete. New factor = {:.4f}".format(self.temp_scale_factor))
    def get_ranged_perm_scale_factor(self, rough_weight):
        if rough_weight < 250:
            return self.perm_scale_factors[0] # 1415.1
        elif rough_weight < 750:
            return self.perm_scale_factors[1] # 1415.0
        elif rough_weight < 1250:
            return self.perm_scale_factors[2] # 1414.9
        elif rough_weight < 1750:
            return self.perm_scale_factors[3] # 1414.8
        elif rough_weight < 2250:
            return self.perm_scale_factors[4] # 1414.7
        elif rough_weight < 2750:
            return self.perm_scale_factors[5] # 1414.6
        else:
            return self.perm_scale_factors[6] # 1414.5
    def save_perm_calibration(self):
        with open("calibration.txt", "w") as file:
            for i in range(len(self.perm_scale_factors)):
                file.write(str(self.perm_scale_factors[i]) + "\n")
                # writes perm scale factors for 100, 500, 1000, 
                # 1500, 2000, 2500, and 3000 (in order) to calibration.txt
    def load_perm_calibration(self):
        try:
            loaded_factors = []

            with open("calibration.txt", "r") as file:
                for _ in range(7):
                    line = file.readline()
                    if not line:
                        return False
                    loaded_factors.append(float(line))

            self.perm_scale_factors = loaded_factors
            return True

        except:
            return False
class AlphaTrimmedMovingAverage:
    def __init__(self, window_size=10, alpha=0.2):
        self.window_size = window_size
        self.alpha = alpha
        self.buffer = []
    def update(self, new_value):
        self.buffer.append(new_value)
        if len(self.buffer) > self.window_size:
            self.buffer.pop(0)
    def get_alpha_moving_average(self):
        n = len(self.buffer)
        sorted_buffer = sorted(self.buffer)
        trim_count = int(n * self.alpha)
        if trim_count * 2 >= n:
            return sorted_buffer[n//2]
        trimmed_values = sorted_buffer[trim_count : n - trim_count]
        return sum(trimmed_values) / len(trimmed_values)
    def reset_alpha_moving_average(self):
        self.buffer = []
    def is_ready(self):
        return len(self.buffer) >= self.window_size
class TJCDisplay:
    END = b'\xff\xff\xff'
    def __init__(self, uart):
        self.uart = uart
        self.text_buffer = ""

    def send_command(self, command):
        self.uart.write(command.encode('utf-8') + self.END)

    def set_value(self, component_name, value): # to send converted weights to display
        command = '{}.val={}'.format(component_name, int(value))
        self.send_command(command)

    def set_text(self, component_name, text): 
        safe_text = str(text).replace('"', '\\"')
        command = '{}.txt="{}"'.format(component_name, safe_text)
        self.send_command(command)

    def change_page(self, page_name):
        self.send_command("page {}".format(page_name))

    def get_command(self):
        line = self.uart.readline()

        if not line:
            return None

        print("RAW command from display:", line)

        line = line.rstrip(b"\r\n")  # better than strip() for binary packets

        print("Cleaned command from display:", line)

        return line

DOUT_PIN = 4   # HX711 DT / DOUT
SCK_PIN = 5    # HX711 SCK
scale = HX711(DOUT_PIN, SCK_PIN)

filter_window_size = 10
filter_alpha_factor = 0.25
weight_filter = AlphaTrimmedMovingAverage(filter_window_size, filter_alpha_factor)

DISPLAY_UART_ID = 1
MCU_TX_DISPLAY_RX_PIN = 18
MCU_RX_DISPLAY_TX_PIN = 17
DISPLAY_BAUDRATE = 115200
display_uart = UART(
    DISPLAY_UART_ID,
    baudrate=DISPLAY_BAUDRATE,
    tx=Pin(MCU_TX_DISPLAY_RX_PIN), # pin that sends data from ESP32-S3 to display
    rx=Pin(MCU_RX_DISPLAY_TX_PIN) # pin that receives data from display to ESP32-S3
)

display = TJCDisplay(display_uart)

# variables
use_perm_scale_factors = True
last_displayed_weight = None
in_weighing_page = False
in_multi_calibration_page = False
in_single_calibration_page = False
placed_count = 0
if scale.load_perm_calibration():
    print("Permanent calibration loaded.")
else:
    print("Using default permanent scale factors.")

while True:
    command = display.get_command()

    if command:
        print("MCU received command:", command)

        if command == b"WEIGH":
            in_weighing_page = True
            in_multi_calibration_page = False
            in_single_calibration_page = False
        elif command == b"S_CAL":
            in_multi_calibration_page = False
            in_weighing_page = False
            in_single_calibration_page = True
        elif command == b"M_CAL":
            in_single_calibration_page = False
            in_multi_calibration_page = True
            in_weighing_page = False
        
        if in_weighing_page:
            if command == b"TARE":
                # print("TARE command recognized")
                display.change_page("waiting")
                display.set_text("waiting.t_status", "Remove all weights. Taring...")
                scale.set_offset()
                weight_filter.reset_alpha_moving_average()
                display.set_text("waiting.t_status", "Taring finished.")
                display.change_page("weigh")
                display.set_text("waiting.t_status", "")
            elif command == b"BACK_W":
                # display.set_text("waiting.t_status", "")
                in_weighing_page = False
            else:
                # get ADC
                weight_filter.update(scale.read())
                filtered_ADC = weight_filter.get_alpha_moving_average()
                # get scale factor
                if use_perm_scale_factors:
                    rough_weight = (
                        filtered_ADC - scale.offset
                    ) / scale.fixed_scale_factor_for_perm_weight_estimation
                    selected_scale_factor = scale.get_ranged_perm_scale_factor(rough_weight)
                else:
                    selected_scale_factor = scale.temp_scale_factor
                # calculate weight
                untruncated_weight = (
                    filtered_ADC - scale.offset
                ) / selected_scale_factor
                # proccess weight
                truncated_weight = int(untruncated_weight * 10) / 10
                if abs(truncated_weight) <= 0.1:
                    truncated_weight = 0.0
                displayed_weight = int(truncated_weight * 10)

                # if displayed_weight != last_displayed_weight:
                #     print("Sending weight to display:", displayed_weight)
                #     last_displayed_weight = displayed_weight

                # send weight
                display.set_value("weigh.x_weight", displayed_weight)
        elif in_multi_calibration_page:
            if placed_count <=6:
                display.set_value("multi_cali.p_cal_weight", scale.perm_calibration_weights[placed_count])
            if command == b"PLACED":
                if placed_count <=6: 
                    display.change_page("waiting")
                    display.set_text("waiting.t_status", "Collecting samples...")
                    weight_filter.reset_alpha_moving_average()
                    for _ in range(weight_filter.window_size):
                        weight_filter.update(scale.read())
                    filtered_ADC = weight_filter.get_alpha_moving_average()
                    display.set_text("waiting.t_status", "Calculating calibration...")
                    untruncated_scale_factor = (filtered_ADC - scale.offset) / scale.perm_calibration_weights[placed_count]
                    truncated_scale_factor = int(untruncated_scale_factor * 10) / 10
                    scale.perm_scale_factors[placed_count] = truncated_scale_factor
                    if placed_count <=5:
                        display.set_text("waiting.t_status", "Place next calibration weight...")
                        display.change_page("multi_cali")
                        display.set_text("waiting.t_status", "")
                    placed_count += 1
                    if placed_count == 7:
                        scale.save_perm_calibration()
                        display.set_text("waiting.t_status", "All calibrations permanently saved.")
                        display.change_page("multi_cali")
                        display.set_text("waiting.t_status", "")     
            elif command == b"BACK_M":
                if placed_count <=6: 
                    display.change_page("waiting")
                    display.set_text("waiting.t_status", "Calibration not saved.") 
                    scale.load_perm_calibration()
                    # is the following code necessary? 
                    # if scale.load_perm_calibration():
                    #     print("Permanent calibration loaded.")
                    # else:
                    #     print("Using default permanent scale factors.")
                    sleep_ms(1000)
                    display.change_page("multi_cali")
                    display.set_text("waiting.t_status", "") 
                # display.set_text("waiting.t_status", "")
                placed_count = 0
                in_multi_calibration_page = False 
        elif in_single_calibration_page:
            if command.startswith(b"CAL:") and len(command) == 6:
                # print("temp CAL command recognized")
                temp_cal_weight = int.from_bytes(command[4:6], byteorder='little')
                # print("Calibration weight received:", temp_cal_weight)
                if temp_cal_weight > 0:
                    display.change_page("waiting")
                    display.set_text("waiting.t_status", "Collecting samples and calculating calibration...")
                    scale.set_temp_scale_factor(temp_cal_weight)
                    display.set_text("waiting.t_status", "Calibration saved.")
                    display.change_page("single_cali")
                    display.set_text("waiting.t_status", "")
                    use_perm_scale_factors = False
                else:
                    display.change_page("waiting")
                    display.set_text("waiting.t_status", "Error: Calibration weight must be a positive number.")
                    sleep_ms(1000)
                    display.change_page("single_cali")
                    display.set_text("waiting.t_status", "") 
            elif command == b"BACK_S":
                # display.set_text("waiting.t_status", "")
                in_single_calibration_page = False
        else:
            print("Unknown command:", command) 