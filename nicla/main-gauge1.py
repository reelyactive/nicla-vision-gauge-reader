# rename to main.py to run on the nicla. Make sure that my_functions.py is also on the nicla device

# image library: https://docs.openmv.io/library/omv.image.html#
# Sensor library: https://docs.openmv.io/library/omv.sensor.html
import sensor, image, time, math

#import my resused functions and config vars
import my_functions as my
import my_config
config = my_config.get_config()

#import ble functions
import my_ble


################ SETTING CONFIG VARS
# set to this when we're using real gauges and stickers instead of images on a computer
#thresholds = sticker_thresholds
thresholds = config["color_thresholds"]


# Define the known points and their corresponding measurement marks
# for the below, assume 0 radians is straight down
# NOTE: these values get overridden when colored dots are detected
radian_point_min = config["radian_point_min"] # the point in radians of the min gauge value
marker_min =  config["marker_min"]   # the min gauge value
radian_point_max =  config["radian_point_max"] # the point in radians of the max gauge value
marker_max =  config["marker_max"] # the max gauge value
max_radians = config["max_radians"]

# screen dimensions
width = config["screen_width"]
height = config["screen_height"]

# center point
midx = config["center_x"]
midy = config["center_y"]

# the radius, from the center point,
# of the two circles used to identify a needle line
outer_detect_radius = config["outer_detect_radius"]
inner_detect_radius = config["inner_detect_radius"]

# configs for the sensor
framesize = config["framesize"]
enable_lens_corr = config["enable_lens_corr"]

# the size of the running average list
running_avg_size = config["running_avg_size"]

use_color_dots = config["use_color_dots"]

############# END SETTING CONFIG VARS


# defaults for these values, which will be calculated later based on algorithms for finding the center of the gauge
cmidx = midx
cmidy = midy


# sensor setup
sensor.reset()
sensor.set_pixformat(sensor.RGB565)

# sensor.set_framesize(sensor.QQVGA)  # sensor.QQVGA: 160x120
sensor.set_framesize(framesize) # this approach seems to get me better color for some reason
sensor.set_windowing(width, height)

sensor.skip_frames(time = 2000)
sensor.set_auto_whitebal(False)  # must be turned off for color tracking


# clock setup
clock = time.clock()


# store latest_* values, because in some ticks we won't find any
latest_angle = 0  # most recently measured angle (radians)
latest_gauge_value = (0.0,0.0) # most recently measured gauge value
latest_reading_point = False
latest_center_circle_coords = False
latest_longest_needle_line = False

# running average value
avg_value = 0

while(True):
    clock.tick()
    cmin = False
    cmax = False

    # capture image
    img = sensor.snapshot()
    if enable_lens_corr: img.lens_corr(1.8) # for 2.8mm lens...

    # print out the rgb value in the center pixel.
    # Used to identify colors that can be used for color tracking
    print(image.rgb_to_lab(img.get_pixel(int(midx), int(midy))))

    if(use_color_dots):
        cmin = my.get_min_center(img, thresholds)
        cmax = my.get_max_center(img, thresholds)

        # find the circle in the center of the gauge
        centermost_circle_coords = my.get_center_circle_coords(img, thresholds)

        # update the computed center point
        if(latest_center_circle_coords):
            cmidx = latest_center_circle_coords[0]
            cmidy = latest_center_circle_coords[1]

        # if there's min and max dots, and a center,
        # then determine the angles and use those values to set the
        # radian_point_min and radian_point_max values
        if(cmin and cmax and latest_center_circle_coords):
            radian_point_min = my.rotate_radians(my.get_angle(cmidx, cmidy, cmin[0], cmin[1], height), max_radians)
            radian_point_max = my.rotate_radians(my.get_angle(cmidx, cmidy, cmax[0], cmax[1], height), max_radians)

    if(use_color_dots == False):
        # calculate the cmin and cmax coordinate based on the radians values?
        cmin = my.polar_to_rectangular(outer_detect_radius, radian_point_min, cmidx, cmidy)
        cmax = my.polar_to_rectangular(outer_detect_radius, radian_point_max, cmidx, cmidy)
        centermost_circle_coords = (cmidx, cmidy,5)

    # if we found a center circle, hang on to it for times when we don't find one
    if(centermost_circle_coords):
        latest_center_circle_coords = centermost_circle_coords

    longest_needle_line = False
    longest_needle_len = 0


    # find the longest gauge needle line
    l = my.get_longest_needle_line(img, cmidx, cmidy, inner_detect_radius, outer_detect_radius)
    if(l):
        longest_needle_line = l
        longest_needle_len = my.line_length(l)

    # if we find a needle line, save it for the times when we don't find one, and compute these other values.
    if(longest_needle_line):
        # save this line value
        latest_longest_needle_line = longest_needle_line
        # get the the point that represents where the gauge needle is pointing
        latest_reading_point = my.line_circle_intersect_point(longest_needle_line, cmidx, cmidy, outer_detect_radius)
        # determine that lines angle
        latest_angle = my.get_angle(cmidx, cmidy, latest_reading_point[0], latest_reading_point[1], height)
        # now get the value of the gauge, based on that value
        latest_gauge_value = my.radians_to_measurement(latest_angle, radian_point_min, radian_point_max, marker_min, marker_max, max_radians)

        # maintain a running average, to even out the values a bit.
        # especially since the line detection tends to flip back and forth
        # btw opposite sides of the needle, giving slightly different values
        avg_value = my.update_running_avg_value(latest_gauge_value[0], running_avg_size)
        # this will be the value we publish.


    ########### SENDING VALUE ###############
    my_ble.send_value(avg_value)



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

    # draw lines from the min and max circles to the center point of the gauge
    if(cmin and cmax and latest_center_circle_coords):
        img.draw_line(int(cmidx), int(cmidy), int(cmin[0]), int(cmin[1]), color = (0,255,0),thickness=3)
        img.draw_line(int(cmidx), int(cmidy), int(cmax[0]), int(cmax[1]), color = (0,255,0),thickness=3)

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
    if(cmin):
        img.draw_circle(int(cmin[0]), int(cmin[1]), 3, color = (255, 0, 0), thickness = 3, fill = False)
    # draw a circle around the found GmaxREEN dot
    if(cmax):
        img.draw_circle(int(cmax[0]), int(cmax[1]), 3, color = (0, 255, 0), thickness = 3, fill = False)

