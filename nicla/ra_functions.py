import math
import ra_config




# Only blobs that with more pixels than "pixel_threshold" and more area than "area_threshold" are
# returned by "find_blobs" below. Change "pixels_threshold" and "area_threshold" if you change the
# camera resolution. "merge=True" merges all overlapping blobs in the image.
# RGB to LAB: https://products.aspose.app/svg/color-converter/rgb-to-lab
def get_color_center(img, thresh):
    center = False
    for blob in img.find_blobs(
        [thresh],
        pixels_threshold=50, #200
        area_threshold=50, #200
        merge=True,
    ):
        center = blob
    # let's hope there's just one
    if(center):
        return(center.cx(), center.cy(), 5)
    return False



# functions for finding colored spots. Uses the threshold array's elements
def get_red_center(img, thresholds):
    return get_color_center(img, thresholds["red"])

def get_green_center(img, thresholds):
    return get_color_center(img, thresholds["green"])

def get_blue_center(img, thresholds):
    return get_color_center(img, thresholds["blue"])

def get_yellow_center(img, thresholds):
    return get_color_center(img, thresholds["yellow"])

def get_min_center(img, thresholds):
    config = my_config.get_config()
    return get_color_center(img, thresholds[config["min_color"]])

def get_max_center(img, thresholds):
    config = my_config.get_config()
    return get_color_center(img, thresholds[config["max_color"]])

def get_center_center(img, thresholds):
    config = my_config.get_config()
    return get_color_center(img, thresholds[config["center_color"]])


def get_center_circle_coords(img, thresholds):
    coords = get_center_center(img, thresholds)
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





# get the distance between two points
def distance (x0, y0, x1, y1):
    return math.sqrt((x1-x0)**2 + (y1-y0)**2)

# get the length of a line l
def line_length(l):
    return distance(l.x1(), l.y1(), l.x2(), l.y2())

# return true if the given line segment intersects the given circle
def line_intersects_circle( x0,y0, x1,y1, cx, cy, r ):
    if distance(x0,y0,cx,cy) < r and distance(x1,y1,cx,cy) > r:
        return True
    if distance(x0,y0,cx,cy) > r and distance(x1,y1,cx,cy) < r:
        return True
    return False

# find the point or points where a line segment intersects a circle
def circle_line_intersection(cx, cy, r, x1, y1, x2, y2):
    # Calculate the direction vector of the line segment
    dx = x2 - x1
    dy = y2 - y1

    # Calculate the vector from the line segment's starting point to the circle's center
    fx = x1 - cx
    fy = y1 - cy

    a = dx * dx + dy * dy
    b = 2 * (fx * dx + fy * dy)
    c = fx * fx + fy * fy - r * r

    discriminant = b * b - 4 * a * c

    if discriminant < 0:
        return False  # No intersection

    t1 = (-b + math.sqrt(discriminant)) / (2 * a)
    t2 = (-b - math.sqrt(discriminant)) / (2 * a)

    if 0 <= t1 <= 1:
        x_inter1 = x1 + t1 * dx
        y_inter1 = y1 + t1 * dy
        intersection1 = (x_inter1, y_inter1)
    else:
        intersection1 = None

    if 0 <= t2 <= 1:
        x_inter2 = x1 + t2 * dx
        y_inter2 = y1 + t2 * dy
        intersection2 = (x_inter2, y_inter2)
    else:
        intersection2 = None

    if intersection1 and intersection2:
        return intersection1, intersection2
    elif intersection1:
        return intersection1
    elif intersection2:
        return intersection2
    else:
        return False

# get intersetion point(s) for line l and circle defined by cx, cy, cr
def line_circle_intersect_point(l, cx, cy, cr):
    if(l ):
        return circle_line_intersection(cx, cy, cr, l.x1(), l.y1(), l.x2(), l.y2())
    return False

# convert the supplied radian measurement to a gauge measurment.
# uses some global variables
# radian_point_min - location of min value in radians
# radian_point_max - locaiton of max value in radians
# marker_min - the min marker value
# marker_max - the max marker value
# max_radians - 0 the number of radians in a circle

def rotate_radians(radians, max_radians):
    # reverse it
    radians = (max_radians) - radians
    # put 0 at the bottom
    radians = radians - (.5 * math.pi)
    if(radians < 0):
        radians = (max_radians) +  radians
    return radians


def radians_to_measurement(radians, radian_point_min, radian_point_max, marker_min, marker_max, max_radians):
    # reverse it
    radians = rotate_radians(radians, max_radians)
    rad_range = radian_point_max - radian_point_min
    marker_scale = (marker_max - marker_min) / rad_range
    measurement_mark = ((radians - radian_point_min) * marker_scale) + marker_min
    return (measurement_mark, radians / math.pi)


# used by get_angle
def angle_trunc(a):
    while a < 0.0:
        a += math.pi * 2
    return a

# get angle, in radians, of a given line segment. Angle is counter-clockwise against a horizontal line
def get_angle(x_orig, y_orig, x_landmark, y_landmark, height):
    y_orig = float(height) - y_orig
    y_landmark = float(height) - y_landmark
    deltaY = y_landmark - y_orig
    deltaX = x_landmark - x_orig
    return angle_trunc(math.atan2(deltaY, deltaX))

# get angle of line l
def line_angle(l):
    return get_angle(l.x1(), l.y1(), l.x2(), l.y2())


running_avg_list = []
running_avg_value = 0

# maintain a running average
def update_running_avg_value(value, running_avg_size):
    global running_avg_value
    global running_avg_list
    if(len(running_avg_list) >= running_avg_size):
        running_avg_list.pop(0)
    running_avg_list.append(value)
    sumv = 0
    for num in running_avg_list:
        sumv += num
    running_avg_value = sumv / len(running_avg_list)
    return running_avg_value


# get the circle closest to the center
# ie, smallest that has the center of the image inside it
def get_center_circle(img):

    centermost_circle = False
    min_dist = 1000
    min_r = 1000
    for c in img.find_circles(
    #        threshold=2000,
        threshold=3500,
        x_margin=10,
        y_margin=10,
        r_margin=10,
        r_min=2,
        r_max=100,
        r_step=2,
    ):

        # distance to center
        d_to_c = distance(c.x(), c.y(), midx, midy);
        if(d_to_c < center_detect_thresh and d_to_c < min_dist):
            centermost_circle = c
            min_dist = d_to_c

    return centermost_circle


def polar_to_rectangular(radius, angle, x_c, y_c):
    #angle = rotate_radians(angle, 2 * math.pi)
    # Convert angle from radians to degrees
    angle = angle + (.5 * math.pi)
    angle_degrees = math.degrees(angle)

    # Calculate the x and y coordinates in rectangular form
    x = x_c + radius * math.cos(angle)
    y = y_c + radius * math.sin(angle)

    return x, y

# `threshold` controls how many lines in the image are found. Only lines with
# edge difference magnitude sums greater than `threshold` are detected...

# More about `threshold` - each pixel in the image contributes a magnitude value
# to a line. The sum of all contributions is the magintude for that line. Then
# when lines are merged their magnitudes are added togheter. Note that `threshold`
# filters out lines with low magnitudes before merging. To see the magnitude of
# un-merged lines set `theta_margin` and `rho_margin` to 0...

# `theta_margin` and `rho_margin` control merging similar lines. If two lines
# theta and rho value differences are less than the margins then they are merged.

def get_longest_needle_line(img, cx, cy, inner_detect_radius, outer_detect_radius):
    longest_needle_line = False
    longest_needle_len = 0
    for l in img.find_line_segments(threshold = 1500, theta_margin = 50, rho_margin = 50):
        color = (255, 0, 0)
        if line_intersects_circle(l.x1(), l.y1(),l.x2(), l.y2(), cx, cy, inner_detect_radius):
            color = (255, 0, 0)
            if line_intersects_circle(l.x1(), l.y1(),l.x2(), l.y2(),cx, cy, outer_detect_radius):
                color = (0,255,255)
                if(line_length(l) > longest_needle_len):
                    longest_needle_line = l
                    longest_needle_len = line_length(l)
    return longest_needle_line



