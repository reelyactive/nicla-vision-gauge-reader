# rename to main.py to run on the nicla. Make sure that my_functions.py is also on the nicla device

# image library: https://docs.openmv.io/library/omv.image.html#
# Sensor library: https://docs.openmv.io/library/omv.sensor.html
import sensor, image, time, math

#import my resused functions
import my_functions as my

enable_lens_corr = False # turn on for straighter lines...
#enable_lens_corr = True # turn on for straighter lines...

# sensor setup
sensor.reset()
sensor.set_pixformat(sensor.RGB565) # grayscale is faster

# sensor.set_framesize(sensor.QQVGA)  # sensor.QQVGA: 160x120
sensor.set_framesize(sensor.QVGA) # this approach seems to get me better color for some reason
sensor.set_windowing(160, 120)

sensor.skip_frames(time = 2000)
sensor.set_auto_whitebal(False)  # must be turned off for color tracking

clock = time.clock()

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

# set to this when we're using real gauges and stickers instead of images on a computer
thresholds = sticker_thresholds


# Define the known points and their corresponding measurement marks
# for the below, assume 0 radians is straight down
# NOTE: these values get overridden when colored dots are detected
radian_point_min = .25 * math.pi # the point in radians of the min gauge value
marker_min = 0   # the min gauge value
radian_point_max = 1.75 * math.pi  # the point in radians of the max gauge value
marker_max = 100 # the max gauge value

max_radians = 2 * math.pi

# screen dimensions
width = 160
height = 120

# center point
midx = width / 2
midy = height / 2
# defaults for these values, which will be calculated later based on algorithms for finding the center of the gauge
cmidx = midx
cmidy = midy

outer_detect_radius = 40
inner_detect_radius = 25

# functions for finding colored spots. Uses the threshold array's elements
def get_red_center(img):
    return my.get_color_center(img, thresholds[0])

def get_green_center(img):
    return my.get_color_center(img, thresholds[1])

def get_blue_center(img):
    return my.get_color_center(img, thresholds[2])

def get_yellow_center(img):
    return my.get_color_center(img, thresholds[3])

def get_center_center(img):
    return my.get_color_center(img, thresholds[4])


def get_center_circle_coords(img):
    coords = get_center_center(img)
    '''
    # leaving this in in case we want a dot-less approach to finding the center of the gauge
    if(coords == False):
        circle = get_center_circle(img)
        if(circle):
            coords = (circle.x(), circle.y(), circle.r())
    else:
        coords = [coords[0], coords[1], 20]
    '''
    return coords

# store latest_* values, because in some ticks we won't find any
latest_angle = 0  # most recently measured angle (radians)
latest_gauge_value = (0.0,0.0) # most recently measured gauge value
latest_reading_point = False
latest_center_circle_coords = False
latest_longest_needle_line = False

avg_value = 0

while(True):
    clock.tick()
    img = sensor.snapshot()
    if enable_lens_corr: img.lens_corr(1.8) # for 2.8mm lens...

    # print out the rgb value in the center pixel.
    # Used to identify colors that can be used for color tracking
    print(img.get_pixel(int(midx), int(midy)))

    cred = get_red_center(img)
    cgreen = get_green_center(img)
    cblue = get_blue_center(img)
    cyellow = get_yellow_center(img)

    centermost_circle_coords = get_center_circle_coords(img)

    if(centermost_circle_coords):
        latest_center_circle_coords = centermost_circle_coords

    if(latest_center_circle_coords):
        cmidx = latest_center_circle_coords[0]
        cmidy = latest_center_circle_coords[1]

    # if there's green and red dots, and a center,
    # then determine the angles and use those values to set the
    # radian_point_min and radian_point_max values
    if(cred and cgreen and latest_center_circle_coords):
        radian_point_min = my.rotate_radians(my.get_angle(cmidx, cmidy, cred[0], cred[1], height), max_radians)
        radian_point_max = my.rotate_radians(my.get_angle(cmidx, cmidy, cgreen[0], cgreen[1], height), max_radians)


    longest_needle_line = False
    longest_needle_len = 0

    l = my.get_longest_needle_line(img, cmidx, cmidy, inner_detect_radius, outer_detect_radius)
    if(l):
        longest_needle_line = l
        longest_needle_len = my.line_length(l)

    if(longest_needle_line):
        latest_reading_point = my.line_circle_intersect_point(longest_needle_line, cmidx, cmidy, outer_detect_radius)
        latest_angle = my.get_angle(cmidx, cmidy, latest_reading_point[0], latest_reading_point[1], height)
        latest_gauge_value = my.radians_to_measurement(latest_angle, radian_point_min, radian_point_max, marker_min, marker_max, max_radians)
        latest_longest_needle_line = longest_needle_line
        avg_value = my.update_running_avg_value(latest_gauge_value[0])
    #         img.draw_line(x0, y0, x1, y1, color = (r, g, b), thickness = 2)

    ###################### Drawing Results to the Image ##############################

    # draw the gauge value on the image
    img.draw_string(50, 70, str(avg_value), color= (255,0,0),scale = 2 )
    # img.draw_string(50, 30, str(latest_gauge_value[1]), color= (color),scale = 2 )

    # draw the identified needle line
    if(latest_longest_needle_line):
        img.draw_line(latest_longest_needle_line.line(), color = (0,0,255),thickness=3)

    # draw a circle where the needle meets the outer gauge identification circle (aka the Reading Point)
    if(latest_reading_point):
        img.draw_circle(int(latest_reading_point[0]), int(latest_reading_point[1]), 3, color = (0,0,255), thickness = 2, fill = False)

    # draw lines from the green and read circles to the center point of the gauge
    if(cred and cgreen and latest_center_circle_coords):
        img.draw_line(cmidx, cmidy, cred[0], cred[1], color = (0,255,0),thickness=3)
        img.draw_line(cmidx, cmidy, cgreen[0], cgreen[1], color = (0,255,0),thickness=3)

    # draw the inner circle through which the needle line muct cross
    img.draw_circle(int(cmidx), int(cmidy), outer_detect_radius, color = (255, 255, 0), thickness = 1, fill = False)
    # draw the outer circle through which the needle line muct cross
    img.draw_circle(int(cmidx), int(cmidy), inner_detect_radius, color = (255, 255, 0), thickness = 1, fill = False)

    # draw a circle at the center of the image
    img.draw_circle(int(midx), int(midy), 3, color = (0, 255, 0), thickness = 1, fill = False)

    # draw a circle at the identified center of the gauge
    if(latest_center_circle_coords):
        img.draw_circle(latest_center_circle_coords[0], latest_center_circle_coords[1], latest_center_circle_coords[2], color=(0, 0, 0), thickness=4)
    # draw a cirle around the found RED dot
    if(cred):
        img.draw_circle(cred[0], cred[1], 3, color = (255, 0, 0), thickness = 3, fill = False)
    # draw a circle around the found GREEN dot
    if(cgreen):
        img.draw_circle(cgreen[0], cgreen[1], 3, color = (0, 255, 0), thickness = 3, fill = False)



