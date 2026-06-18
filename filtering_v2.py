# Things to still do: 
# 1. set up communication between display buttons and MCU (use booleans)
    # if (calibration_button_pressed): 
        # calibration_weight = get value (hex) entered into keypad from display upon hitting OK sign
        # scale.set_scale_factor(calibration_weight)
    # if (tare_button_pressed):
        # scale.set_offset() 
# 2. decrease delay in between displayed weights

from machine import Pin
from time import sleep_us, sleep_ms

class HX711:
    def __init__(self, dout_pin, sck_pin, gain=128):
        self.dout = Pin(dout_pin, Pin.IN)
        self.sck = Pin(sck_pin, Pin.OUT)
        self.sck.value(0)
        self.offset = 0
        self.calibration_weight = 1
        self.calibration_scale_factor = 1414.8 
        self.moving_average_buffer = []
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
    def set_scale_factor(self, calibration_weight):
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
        print("Previous scale factor:", self.calibration_scale_factor)
# ***********************
        untruncated_scale_factor = (adc_median - self.offset) / calibration_weight
        truncated_scale_factor = int(untruncated_scale_factor * 10) / 10
        self.calibration_scale_factor = truncated_scale_factor
# ***********************
        print("Untruncated scale factor:", untruncated_scale_factor)
        print("Truncated and stored scale factor:", self.calibration_scale_factor)
        # print("Calibration complete. New factor = {:.4f}".format(self.calibration_scale_factor))
    def get_scale_factor(self):
        return self.calibration_scale_factor
    def get_cal_weight(self): 
        return self.calibration_weight
    # Median filter
    def get_median_filtered_reading(self, size = 5):
        readings = []
        for _ in range(size):
            readings.append(self.read())
            sleep_ms(10)
        readings.sort()
        middle_index = size // 2
        return readings[middle_index]
    # Moving average filter
    def get_moving_average(self, new_value, size = 10):
        self.moving_average_buffer.append(new_value)
        if len(self.moving_average_buffer) > size:
            self.moving_average_buffer.pop(0)
        return sum(self.moving_average_buffer) / len(self.moving_average_buffer)
    def reset_moving_average(self):
        self.moving_average_buffer = []
    def get_scale_factor_for_weight(self, rough_weight):
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

# initalizing HX711
DOUT_PIN = 4   # HX711 DT / DOUT
SCK_PIN = 5    # HX711 SCK
scale = HX711(DOUT_PIN, SCK_PIN)

# initializing AlphaTrimmedMovingAverage
alpha_window_size = 10
alpha_factor = 0.25
alpha = AlphaTrimmedMovingAverage(alpha_window_size, alpha_factor)

# Variables
# VOFA_LABEL = "scale"
median_filter_size = 5
moving_average_filter_size = 2

# Setup equivalent
print("Taring will start in 3 seconds. Make sure there is NO weight on the scale.")
sleep_ms(3000)
scale.set_offset()

# Loop equivalent
while True:
    # # Step 1: read and median-filter raw ADC values
    # median_filtered_raw = get_median_filtered_reading()
    # # Step 2: apply moving average filter
    # smoothed_raw = get_moving_average(median_filtered_raw)
    # Step 3: subtract offset after filtering
    instruction = input("Enter 1 for calibration, 2 for taring, and anything else for just seeing the weight: ")
    if (instruction == "1"):
        print("Please place the calibration weight on the scale.")
        calibration_weight = int(input("Enter the calibration weight: "))
        scale.set_scale_factor(calibration_weight)
    elif (instruction == "2"):
        print("Current offset is set at", scale.get_offset())
        scale.set_offset() 
    else: 
        # print("Vofa+ output starting...")
        known_weight = input("Enter the weight placed onto the scale: ")
        scale.reset_moving_average()
        alpha.reset_alpha_moving_average()
        count = 0
        while (True):
            alpha.update(scale.read())
            offset = scale.get_offset()
            filtered_ADC = alpha.get_alpha_moving_average()
            rough_weight = (filtered_ADC - offset) / scale.get_scale_factor()
            selected_scale_factor = scale.get_scale_factor_for_weight(rough_weight)
            weight = (filtered_ADC - offset) / selected_scale_factor
            # median_filtered_raw = scale.get_median_filtered_reading(median_filter_size)
            # weight = scale.get_moving_average((median_filtered_raw - scale.get_offset()) / scale.get_scale_factor(), moving_average_filter_size)
            displayed_weight = round(weight, 1)
            # if abs(displayed_weight) < 0.2:
            #     displayed_weight = 0.0
            # VOFA+ output format: "scale:value_without_offset"
            # print("{}:{}".format(VOFA_LABEL, weight))
            if len(alpha.buffer) >= alpha.window_size:
                print("displayed weight: {} g\tmeasured weight: {}\tknown weight: {}\tadc: {}\toffset: {}\tselected scale factor: {}".format(displayed_weight, weight, rough_weight, known_weight, filtered_ADC, offset, selected_scale_factor, scale.get_cal_weight()))
                # print("displayed weight: {:.1f} g\tcalculated weight: {}\tfiltered adc: {}\toffset: {}\tscale_factor: {}\tcal_weight:{}".format(displayed_weight, weight, filtered_ADC, scale.get_offset(), scale.get_scale_factor(), scale.get_cal_weight()))
                print()
                count += 1
                if (count == 20):
                    break