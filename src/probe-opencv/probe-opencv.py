import math
import time
import numpy as np
import cv2

import fxchanger


MAX_VALUE = 9999999999999

MIN_AREA = 50
MAX_AREA = 5000
RECTANGLE_COLOR = (0, 255, 0)
CIRCLE_COLOR = (255, 0, 0)
THRESHOLD_PERCENT = 0.7
FONT = cv2.FONT_HERSHEY_SIMPLEX

cap = cv2.VideoCapture(1)

fps = cap.get(cv2.CAP_PROP_FPS)
width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
distance_coefficient = 30


def message(msg, coord, frame):
    cv2.putText(frame, msg, coord, FONT, 0.4, (255, 255, 255), 1, cv2.LINE_AA)


def rnd_color():
    return np.random.randint(0, 255, (1, 3))[0]


def calc_distance(p1, p2):
    dX = p1.x - p2.x
    dY = p1.y - p2.y
    return math.sqrt(dX * dX + dY * dY)


class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y


class Vector:
    def __init__(self, start, end):
        self.start = start
        self.end = end

    def len(self):
        return calc_distance(self.start, self.end)


class Light:
    def __init__(self, contour, color, timestamp):
        center, radius = cv2.minEnclosingCircle(contour)

        # moments = cv2.moments(contour, False)
        # self.mc = [moments['m10'] / moments['m00'], moments['m01'] / moments['m00']]
        self.contour = contour
        self.color = color
        self.timestamp = timestamp
        self.radius = radius
        self.center = Point(center[0], center[1])
        self.prev = None

    def distance(self, other):
        return Vector(self.center, other.center).len()

    def set_previous(self, prev):
        self.color = prev.color
        self.prev = prev

    def vec(self):
        if self.prev == None:
            return Vector(self.center, self.center)
        else:
            return Vector(prev.center, self.center)

    def speed(self):
        if self.prev == None:
            return 0
        else:
            dT = self.timestamp - self.prev.timestamp
            if dT == 0:
                return 0
            else:
                return self.vec().len() / dT


prev_lights = []
fx = fxchanger.FxChanger()

while (cap.isOpened()):
    start_time = time.time()
    # time.sleep(0.005)

    brightness = cap.get(cv2.CAP_PROP_BRIGHTNESS)
    ret, frame = cap.read()

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    blur = cv2.medianBlur(gray, 15)
    # blur = cv2.GaussianBlur(gray, (7, 7), 8)

    [minVal, maxVal, minLoc, maxLoc] = cv2.minMaxLoc(gray)

    margin = THRESHOLD_PERCENT
    thresh = int(maxVal * margin)
    # print "Threshold: %f" % thresh

    ret, thresh_img = cv2.threshold(blur, thresh, 255, cv2.THRESH_BINARY)
    image, contours, hierarchy = cv2.findContours(thresh_img, cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)

    curr_lights = []

    new_lights = []
    founded_pairs_for_previous_lights = [False] * len(prev_lights)

    for c in contours:
        area = cv2.contourArea(c)
        if (area >= MIN_AREA and area <= MAX_AREA):
            light = Light(c, rnd_color(), start_time)
            curr_lights.append(light)

            # find pair with min distance
            min_prev_distance = MAX_VALUE
            min_prev_idx = -1
            for prev_id, prev in enumerate(prev_lights):
                d = light.distance(prev)
                # print "distance: {}".format(distance)
                if (d < min_prev_distance):
                    min_prev_distance = d
                    min_prev_idx = prev_id

            if min_prev_idx > -1:
                prev = prev_lights[min_prev_idx]
                if (min_prev_distance < (prev.radius + light.radius) / 2 + distance_coefficient):
                    # if (min_prev_distance < distance_coefficient):
                    founded_pairs_for_previous_lights[min_prev_idx] = True
                    new_lights.append(light)
                    light.set_previous(prev)

                    dX = light.center.x - prev.center.x
                    dY = light.center.y - prev.center.y

                    cv2.arrowedLine(frame,
                                    (int(prev.center.x + dX), int(prev.center.y + dY)),
                                    (int(light.center.x + dX * 2), int(light.center.y + dY * 2)),
                                    RECTANGLE_COLOR, 2)

            x, y, w, h = cv2.boundingRect(c)
            # center, radius = cv2.minEnclosingCircle(c)
            # cv2.circle(frame, (int(center[0]),int(center[1])), int(radius), CIRCLE_COLOR, 2);
            cv2.rectangle(frame, (x - 5, y - 5), (x + w + 5, y + h + 5), light.color, 2)
            cv2.circle(frame, (int(light.center.x), int(light.center.y)), 2, CIRCLE_COLOR, 1)

    # lost_lights = []
    # for idx, val in enumerate(founded_pairs_for_previous_lights):
    #     if (val == False):
    #         lost_lights.append(prev_lights[idx])

    for l in curr_lights:
        print l.speed()

    prev_lights = curr_lights

    # cv2.imshow('TrashImage', thresh_img)
    # cv2.imshow('GrayImage', gray)

    end_time = time.time()

    message(
        "Frame size: {} x {}. Fps: {}. Brightness: {}. DistanceC: {}"
            .format(width, height, fps, brightness, distance_coefficient), (10, 20), frame)

    message("Numbers of lights: {}".format(len(curr_lights)), (10, 35), frame)

    message("Frame cost, ms: {}".format((end_time - start_time) * 1000), (10, 50), frame)

    cv2.imshow('FrameImage', frame)

    key = cv2.waitKey(1)
    if key & 0xFF == ord('q'):
        break

    if key & 0xFF == ord('b'):
        cap.set(cv2.CAP_PROP_BRIGHTNESS, brightness + 1.0)

    if key & 0xFF == ord('v'):
        cap.set(cv2.CAP_PROP_BRIGHTNESS, brightness - 1.0)

    if key & 0xFF == ord('m'):
        distance_coefficient = distance_coefficient + 5

    if key & 0xFF == ord('n'):
        distance_coefficient = distance_coefficient - 5

cap.release()
cv2.destroyAllWindows()