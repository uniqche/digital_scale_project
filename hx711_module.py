from machine import Pin
from time import sleep_us, sleep_ms

class HX711:
    def __init__(self, dout_pin, sck_pin, gain=128):
        self.dout = Pin(dout_pin, Pin.IN)
        self.sck = Pin(sck_pin, Pin.OUT)
        self.sck.value(0)

        self.offset = 0
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

    def set_offset(self, offset):
        self.offset = offset

    def get_offset(self):
        return self.offset


# initalizing HX711
DOUT_PIN = 11   # HX711 DT / DOUT
SCK_PIN = 12    # HX711 SCK
scale = HX711(DOUT_PIN, SCK_PIN)

# User-adjustable parameters
OFFSET_SAMPLES = 10
MEDIAN_FILTER_SIZE = 5
MOVING_AVERAGE_SIZE = 10

VOFA_LABEL = "scale"

# Variables
offset_average = 0

moving_average_buffer = [0] * MOVING_AVERAGE_SIZE # creates a list called moving_average_buffer filled with 0s with size MOVING_AVERAGE_SIZE 
moving_average_index = 0
moving_average_filled = False

# Median filter
def get_median_filtered_reading():
     readings = []

     for _ in range(MEDIAN_FILTER_SIZE):
         readings.append(int((scale.read() - offset_average)/10))
         sleep_ms(10)

     readings.sort()
     middle_index = MEDIAN_FILTER_SIZE // 2

     return readings[middle_index]

# # Moving average filter
# def get_moving_average(new_value):
#     global moving_average_index
#     global moving_average_filled

#     moving_average_buffer[moving_average_index] = new_value

#     moving_average_index += 1

#     if moving_average_index >= MOVING_AVERAGE_SIZE:
#         moving_average_index = 0
#         moving_average_filled = True

#     if moving_average_filled:
#         count = MOVING_AVERAGE_SIZE
#     else:
#         count = moving_average_index

#     total = 0

#     for i in range(count):
#         total += moving_average_buffer[i]

#     return total // count


# Setup equivalent
print("HX711 offset calibration starting...")
print("Make sure there is NO weight on the scale.")
sleep_ms(10000)

total = 0

for i in range(OFFSET_SAMPLES):
    reading = scale.read()
    sleep_us(10) 
    total += reading
    print("Offset reading {}: {}".format(i + 1, reading))

offset_average = total // OFFSET_SAMPLES

scale.set_offset(offset_average)

print()
print("Offset calibration finished.")
print("Average offset = {}".format(offset_average))
print("HX711 stored offset = {}".format(scale.get_offset()))

print("Vofa+ output starting...")

# Loop equivalent
while True:
    # # Step 1: read and median-filter raw ADC values
    # median_filtered_raw = get_median_filtered_reading()

    # # Step 2: apply moving average filter
    # smoothed_raw = get_moving_average(median_filtered_raw)

    # Step 3: subtract offset after filtering
    value_without_offset = int((scale.read() - offset_average)/10)
    sleep_ms(10)
    median_filtered_raw = get_median_filtered_reading()

    # # VOFA+ output format: "scale:value_without_offset"
    print("{}:{}".format(VOFA_LABEL, median_filtered_raw))

    sleep_ms(500)

