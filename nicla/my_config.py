import math, sensor

def get_config():
    config_data = {
        "framesize": sensor.QVGA, # this is a preset that specifies the size of the frame that's captured. QVGA is 320x240
        "screen_width" : 160, # the width of the part of the screen that's captured, centered.
        "screen_height" : 120,# the height of the part of the screen that's captured, centered.

        # we define two circles centered around the gauge center
        # if a line passed through both circles, it is considered to be the gauge needle
        # the outer_detect_radius must therefore NOT be intersected by the tail of the gauge
        "outer_detect_radius": 40,
        "inner_detect_radius": 25,


        # if use_color_dots is set to True, then the color thresholds below will be used
        # to find the min, max, and center points on the gauge,
        # overriding the values configured in this file.
        # if False, the cofigured values will be used,
        # use the configured values if you know the gauge will be locked in place relative to the gauge
        "use_color_dots" : True,

        # we need to identify colors used to capture the min and max points on the gauge,
        # and the physical center of the gauge.
        # these colors are defined in terms of a RANGE in the LAB colorspace.
        # (LMin, LMax, AMin, Amax, BMin, BMax)
        # any pixel that is within that range will be identified as that color
        # in real world situations, the same physical color might require a different threshold set,
        # depending on lighting or other conditions.
        # see the README for info on how to create ranges that work for your setup
        # in the array below, create as many named threshold values as you want
        "color_thresholds" : {
            "red": (30, 100, 15, 127, 15, 127),  # red_thresholds (156, 36, 33) -> lab(35.506%, 39.385%, 27.006%)
            # Red Dot is for the LOWEST point on the gauge
            "green" : (20, 95, -40, -10, 0, 30),  # green_thresholds (49, 89, 33)->lab(33.852%, -18.826%, 21.707%)
            # Greeen dot is for the HIGHEST point of the gauge
            "yellow" : (50, 80, -5, 10, 25, 50),  # yellow_thresholds  (206, 174, 90)-> Lab(72.691%, 3.691%, 37.566%)
            # Yellow Dot is for the CENTER.
            "blue" : (-10, 15, 0, 15, -25, 0),  # blue_thresholds (24,16,41)  lab(6.405%, 7.428%, -12.494%)
            # Blue currently not used.
            # add any other colors we want in our arsenal of detectable colors
        },
        # here we map the three points we care about (min, max, center)
        # to one of the named color thresholds above
        "min_color": "red", # the color of the dot at the MINIMUM value of the gauge
        "max_color" : "green",# the color of the dot at the MAXIMUM value of the gauge
        "center_color" : "yellow", # the color of the dot at the CENTER of the gauge

        "enable_lens_corr" : False, # turn on for straighter lines...

        # Define the known points and their corresponding measurement marks
        # for the below, assume 0 radians is straight down
        # NOTE: these values get overridden when colored dots are detected
        # NOTE: Values in radians assume that 0 is STRAIGHT DOWN
        "radian_point_min": .25 * math.pi, # the point in radians of the min gauge value
        "radian_point_max": 1.75 * math.pi,  # the point in radians of the max gauge value
        "marker_min": 0,   # the minimum gauge value
        "marker_max": 100, # the maximum gauge value (keep this value if you want to look at gauges in terms of %-age

        # coordinates of the center of the guage.
        "center_x" : 80,
        "center_y" : 60,

        "running_avg_size": 3, # to smooth out values, we maintain a running average.
        # This is how many values (current and previous) we store to compute that average
        # Higher number = slower change, smoother values
        # Lower Number = faster change, bouncier values
        # because the code often reads opposite sides of of the needle, this causes a small fluctuation
        # averaging the past 2-3 values smooths that out.

        "max_radians": 2 * math.pi, # the number of radians in a circle. This is a math thing and shouldn't need to change

    }



    return config_data;



# Color Tracking Thresholds LAB values (L Min, L Max, A Min, A Max, B Min, B Max)
# The below thresholds track in general red/green/blue things. You may wish to tune them...
# Yellow: lab(97.607%, -12.6%, 74.715%)
# Blue (0,0,255): lab(29.568%, 54.63%, -89.624%)
#blue dot: (99, 109, 255) lab(51.612%, 24.067%, -60.39%)
# test colro 1: rgb(255, 130, 173) lab(70.025%, 41.366%, 0.297%)
# test colro 1: rgb(255, 110, 200) lab(67.224%, 50.431%, -15.106%)
dot_on_screen_thresholds = [
    (30, 100, 15, 127, 15, 127),  # generic_red_thresholds
#    (30, 100, -64, -8, -32, 32),  # generic_green_thresholds
    (70, 100, -80, -50, 40, 80),  # generic_green_thresholds
    (40, 60, 15, 35, -70, -50),  # generic_blue_thresholds
    (80, 120, -20, 0, 65, 84),  # generic_yellow_thresholds
   (60, 80, 40, 60, -20, 10), # center color Thresholds
]

sticker_thresholds = [
    (30, 100, 15, 127, 15, 127),  # red_thresholds (156, 36, 33) -> lab(35.506%, 39.385%, 27.006%)
    (20, 95, -40, -10, 0, 30),  # green_thresholds (49, 89, 33)->lab(33.852%, -18.826%, 21.707%)
    (-10, 15, 0, 15, -25, 0),  # blue_thresholds (24,16,41)  lab(6.405%, 7.428%, -12.494%)
    (50, 80, -5, 10, 25, 50),  # yellow_thresholds  (206, 174, 90)-> Lab(72.691%, 3.691%, 37.566%)
    (50, 80, -5, 10, 25, 50), # center color Thresholds (yellow)
]
