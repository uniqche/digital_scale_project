# changes made from hx711_module_final_with_AlphaTrimmedMovingAverage.py:
# 1. removed median and moving average filter from HX711 class

# things to still do:
# 1. communication with display 

from machine import Pin, UART
from time import sleep_us, sleep_ms

class HX711:
    def __init__(self, dout_pin, sck_pin, gain=128):
        self.dout = Pin(dout_pin, Pin.IN)
        self.sck = Pin(sck_pin, Pin.OUT)
        self.sck.value(0)
        self.offset = 0
        self.calibration_weight = 1
        self.user_defined_scale_factor = 1 
        self.fixed_scale_factor_for_weight_estimation = 1414.8 # do NOT change
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
    def get_offset(self):
        return self.offset
    def set_user_defined_scale_factor(self, calibration_weight):
        self.calibration_weight = calibration_weight
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
        print("Given calibration weight is", calibration_weight)
        # print("Previous scale factor:", self.user_defined_scale_factor)
# ***********************
        untruncated_scale_factor = (adc_median - self.offset) / calibration_weight
        truncated_scale_factor = int(untruncated_scale_factor * 10) / 10
        self.user_defined_scale_factor = truncated_scale_factor
# ***********************
        print("Untruncated scale factor:", untruncated_scale_factor)
        print("Truncated and stored scale factor:", self.user_defined_scale_factor)
        # print("Calibration complete. New factor = {:.4f}".format(self.user_defined_scale_factor))
    def get_cal_weight(self): 
        return self.calibration_weight
    def get_ranged_default_scale_factor(self, rough_weight):
        if rough_weight < 500:
            return 1415.1
        elif rough_weight < 1000:
            return 1415.0
        elif rough_weight < 1500:
            return 1414.9
        elif rough_weight < 2000:
            return 1414.8
        elif rough_weight < 2500:
            return 1414.7
        else:
            return 1414.6
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

    BTN_START_WEIGHING = 0x01
    BTN_WEIGHING_BACK = 0x02
    BTN_TARE = 0x03
    BTN_START_CALIBRATION = 0x04
    BTN_CALIBRATION_BACK = 0x05
    BTN_CALIBRATION_CONFIRM = 0x06

    def __init__(self, uart):
        self.uart = uart
        self.text_buffer = ""

    def send_command(self, command):
        # debug print statements
        print("Sent command: {}{}".format(command.encode('utf-8'), self.END))
        self.uart.write(command.encode('utf-8') + self.END)

    def set_value(self, component_name, value):
        command = '{}.val={}'.format(component_name, int(value))
        self.send_command(command)

    def change_page(self, page_name):
        self.send_command("page {}".format(page_name))

    def read_raw(self): # reads the available bytes and returns them as a bytes object.
        if self.uart.any():
            return self.uart.read() 
        return None

    def read_button_event(self):
        data = self.read_raw()
        if not data:
            return None
        # Check for simple one-byte button packets.
        for b in data:
            if b in (
                self.BTN_START_WEIGHING,
                self.BTN_WEIGHING_BACK,
                self.BTN_TARE,
                self.BTN_START_CALIBRATION,
                self.BTN_CALIBRATION_BACK,
                self.BTN_CALIBRATION_CONFIRM
            ):
                return b

    def read_calibration_weight(self): 
        data = self.read_raw()
        if not data:
            return None
        try:
            self.text_buffer += data.decode('utf-8')
        except UnicodeError:
            return None

        if "\n" not in self.text_buffer:
            return None

        line, self.text_buffer = self.text_buffer.split("\n", 1)
        line = line.strip()

        if line.startswith("CW:"):
            try:
                return float(line[3:])
            except ValueError:
                return None

        return None

# set up (initializations)
DOUT_PIN = 4   # HX711 DT / DOUT
SCK_PIN = 5    # HX711 SCK

DISPLAY_UART_ID = 1
DISPLAY_TX_PIN = 17
DISPLAY_RX_PIN = 18
DISPLAY_BAUDRATE = 115200

display_uart = UART(
    DISPLAY_UART_ID,
    baudrate=DISPLAY_BAUDRATE,
    tx=Pin(DISPLAY_TX_PIN), # pin that sends data from ESP32-S3 to display
    rx=Pin(DISPLAY_RX_PIN) # pin that receives data from display to ESP32-S3
)
display = TJCDisplay(display_uart)

filter_window_size = 10
filter_alpha_factor = 0.25
scale = HX711(DOUT_PIN, SCK_PIN)
filter = AlphaTrimmedMovingAverage(filter_window_size, filter_alpha_factor)

# booleans
weighing = False
weighing_start_up = False
tare_button_pressed = False
weighing_back_button_pressed = False
calibrating = False
calibrating_back_button_pressed = False
calibration_weight_confirmed_is_pressed = False
use_default_scale_factors = True

# loop
while True:
    # checks for buttons
    event = display.read_button_event()

    if event == TJCDisplay.BTN_START_WEIGHING:
        weighing = True
        weighing_start_up = True
        calibrating = False
        # display.change_page("weigh")

    elif event == TJCDisplay.BTN_WEIGHING_BACK:
        weighing_back_button_pressed = True

    elif event == TJCDisplay.BTN_TARE:
        tare_button_pressed = True

    elif event == TJCDisplay.BTN_START_CALIBRATION:
        calibrating = True
        weighing = False
        # display.change_page("calibration")

    elif event == TJCDisplay.BTN_CALIBRATION_BACK:
        calibrating_back_button_pressed = True

    elif event == TJCDisplay.BTN_CALIBRATION_CONFIRM:
        calibration_weight_confirmed_is_pressed = True
    
    if weighing:
        if weighing_start_up:
            display.set_text("t_status", "Taring...")
            display.set_text("t_weight", "--.- g")

            filter.reset_alpha_moving_average()
            scale.set_offset()

            display.set_text("t_status", "Ready")
            weighing_start_up = False

        elif tare_button_pressed:
            display.set_text("t_status", "Taring...")
            scale.set_offset()
            filter.reset_alpha_moving_average()
            display.set_text("t_status", "Ready")
            tare_button_pressed = False

        elif weighing_back_button_pressed:
            weighing = False
            weighing_back_button_pressed = False
            display.change_page("main")

        else:
            filter.update(scale.read())

            if filter.is_ready():
                filtered_ADC = filter.get_alpha_moving_average()

                if use_default_scale_factors:
                    rough_weight = (
                        filtered_ADC - scale.get_offset()
                    ) / scale.fixed_scale_factor_for_weight_estimation

                    selected_scale_factor = scale.get_ranged_default_scale_factor(rough_weight)
                else:
                    selected_scale_factor = scale.user_defined_scale_factor

                non_truncated_weight = (
                    filtered_ADC - scale.get_offset()
                ) / selected_scale_factor

                truncated_weight = round(non_truncated_weight, 1)

                if abs(truncated_weight) <= 0.1:
                    truncated_weight = 0.0

                display.set_text("t_weight", "{:.1f} g".format(truncated_weight))

    elif calibrating:
        if calibrating_back_button_pressed:
            calibrating_back_button_pressed = False
            calibrating = False
            display.change_page("main")

        elif calibration_weight_confirmed_is_pressed:
            display.set_text("t_status", "Reading input...")

            calibration_weight = display.read_calibration_weight()

            if calibration_weight is not None:
                display.set_text("t_status", "Calibrating...")

                scale.set_user_defined_scale_factor(calibration_weight)
                use_default_scale_factors = False

                display.set_text(
                    "t_status",
                    "Factor: {:.1f}".format(scale.user_defined_scale_factor)
                )

                calibration_weight_confirmed_is_pressed = False
                calibrating = False

                weighing = True
                weighing_start_up = True
                display.change_page("weigh")

    # if weighing: # set to True when main page's 称量 button is pressed
    #     if weighing_start_up: # set to True when main page's 称量 button is pressed
    #         filter.reset_alpha_moving_average()
    #         scale.set_offset() 
    #         # send command SF FF FF FF (SF = startup finished); upon receiving this, the display should skip to page weigh 
    #         weighing_start_up = False
    #     elif tare_button_pressed:
    #         scale.set_offset()
    #         # send command TF FF FF FF (TF = tare finished); upon receiving this, the display should skip to page weigh 
    #         tare_button_pressed = False
    #     elif not weighing_start_up:
    #         filter.update(scale.read())
    #         if filter.is_ready():
    #             filtered_ADC = filter.get_alpha_moving_average()
    #             if use_default_scale_factors:
    #                 rough_weight = (filtered_ADC - scale.offset) / scale.fixed_scale_factor_for_weight_estimation
    #                 selected_scale_factor = scale.get_ranged_default_scale_factor(rough_weight)
    #             else:
    #                 selected_scale_factor = scale.user_defined_scale_factor
    #             non_truncated_weight = (filtered_ADC - scale.get_offset()) / selected_scale_factor
    #             truncated_weight = round(non_truncated_weight, 1)
    #             if abs(truncated_weight) <= 0.1:
    #                 truncated_weight = 0.0
    #             # send converted and truncated weights to display 
    #     elif weighing_back_button_pressed:
    #         weighing = False # goes back to home page
    #         weighing_back_button_pressed = False
    # elif calibrating: # set to True when main page's 校准 button is pressed
    #     if calibrating_back_button_pressed: # set to True when calibration page's 返回 button is pressed
    #         calibrating_back_button_pressed = False
    #         calibrating = False # goes back to home page
    #     elif calibration_weight_confirmed_is_pressed: # set to True when calibration page's 确认 button is pressed
    #         # receive hex string from display's va0 variable that's set when keyPad's OK button is pressed 
    #         # process 还原 data packet to get decimal value of calibration weight
    #         # store received calibration weight in "calibration_weight" variable
    #         scale.set_user_defined_scale_factor(calibration_weight)
    #         # computes new scale factor
    #         # truncates new scale factor to 0.1 decimal point
    #         # stores new scale factor in "scale.user_defined_scale_factor"
            
    #         # send command SF FF FF FF (CF = calibration finished); upon receiving this, the display should skip to page weigh 
    #         use_default_scale_factors = False
    #         calibration_weight_confirmed_is_pressed = False
    #         calibrating = False
    #         weighing = True # goes to weighing page
    #         weighing_start_up = True 