from machine import Pin
from time import sleep
from neopixel import NeoPixel
import sys
import random
import select

# initialize the NeoPixel LED
LED_pin=Pin(48, Pin.OUT)    # Pin 38 for v1.1, Pin 48 for v1.0
np=NeoPixel(LED_pin, 1)    # 1 for only one LED
# 24 hardcoded colors for testing purposes
colors = [
    (255, 0, 0),      # red
    (255, 64, 0),     # orange-red
    (255, 128, 0),    # orange
    (255, 191, 0),    # amber
    (255, 255, 0),    # yellow
    (191, 255, 0),    # yellow-green
    (128, 255, 0),    # lime
    (64, 255, 0),     # green-lime
    (0, 255, 0),      # green
    (0, 255, 64),     # spring green
    (0, 255, 128),    # mint
    (0, 255, 191),    # aqua-green
    (0, 255, 255),    # cyan
    (0, 191, 255),    # sky blue
    (0, 128, 255),    # blue-cyan
    (0, 64, 255),     # deep blue
    (0, 0, 255),      # blue
    (64, 0, 255),     # violet-blue
    (128, 0, 255),    # purple
    (191, 0, 255),    # violet
    (255, 0, 255),    # magenta
    (255, 0, 191),    # pink-magenta
    (255, 0, 128),    # pink
    (255, 0, 64)      # rose
]
# more initialization
#color_count = 1
current_color = (255,255,255)
current_brightness_level = 10

# Allows us to check whether VOFA+ sent data without freezing the program
poll = select.poll()
poll.register(sys.stdin, select.POLLIN)

#print("color_count:", color_count)
while (True):
    if poll.poll(0):
        message = sys.stdin.readline().strip() # 24, 5 where 24 = color, and 5 = brightness level. 
        if message == "":
            pass
        else:
            substrings = message.split(",")
            new_color_index = int(substrings[0])
            current_color = colors[new_color_index]
            print("New color: {}".format(current_color))
            new_brightness_level = int(substrings[1])
            current_brightness_level = new_brightness_level
            print("New brightness level: {}".format(current_brightness_level)) 

    brightness_factor = 0.1*current_brightness_level

    r = int(current_color[0] * brightness_factor)
    g = int(current_color[1] * brightness_factor)
    b = int(current_color[2] * brightness_factor)

    np[0] = (r,g,b)
    np.write()
    sleep(1)

    print("Current color: {}".format(current_color))
    print("Current brightness:{}".format(current_brightness_level))


# from machine import Pin
# from time import sleep
# from neopixel import NeoPixel
# import sys
# import random
# import select

# LED_pin=Pin(48, Pin.OUT)    # Pin 38 for v1.1, Pin 48 for v1.0
# np=NeoPixel(LED_pin, 1)    # 1 for only one LED
# color_count = 1

# # Allows us to check whether VOFA+ sent data without freezing the program
# poll = select.poll()
# poll.register(sys.stdin, select.POLLIN)
# brightness_level = 10

# while (color_count < 25):
#     print("color_count:", color_count)
    
#     r = random.randint(0, 255)
#     g = random.randint(0, 255)
#     b = random.randint(0, 255)

#     if poll.poll(0):
#         message = sys.stdin.readline().strip()

#         if message == "":
#             pass
#         else:
#             try:
#                 new_brightness = int(message)

#                 if 0 <= new_brightness <= 10:
#                     brightness_level = new_brightness
#                     print("New brightness level: {}".format(brightness_level))
#                 else:
#                     print("Error: brightness must be from 0 to 10")

#             except ValueError:
#                 print("Error: not a valid integer")
    
#     brightness_factor = 0.1*brightness_level
#     np[0] = (int(r*brightness_factor), int(g*brightness_factor), int(b*brightness_factor))
#     np.write()
#     sleep(1)
#     print("brightness_level:{}".format(brightness_level))
#     color_count = color_count + 1