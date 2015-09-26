import math

import numpy as np
import cv2
import time


MIN_AREA = 100
MAX_AREA = 1200
RECTANGLE_COLOR = (0, 255, 0)
CIRCLE_COLOR = (255, 0, 0)
THRESHOLD_PERCENT = 0.7
FONT = cv2.FONT_HERSHEY_SIMPLEX

cap = cv2.VideoCapture(0)

width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)

def message(msg, coord, frame):
    cv2.putText(frame, msg, coord, FONT, 0.4, (255, 255, 255), 1, cv2.LINE_AA)

def rnd_color():
    return np.random.randint(0, 255, (1, 3))[0]

class Light:
    def __init__(self, contour):
        self.contour = contour

        moments = cv2.moments(contour, False)
        self.mass_center = [moments['m10'] / moments['m00'], moments['m01'] / moments['m00']]
        self.color = rnd_color()

    def distance(self, other):
        x1 = other.mass_center[0]
        x2 = self.mass_center[0]
        y1 = other.mass_center[1]
        y2 = self.mass_center[1]
        return math.sqrt((x2 - x1) * (x2 - x1) + (y2 - y1) * (y2 - y1))

prev_lights = []
start = time.clock();

while (cap.isOpened()):
    ret, frame = cap.read()

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    blur = cv2.medianBlur(gray, 15)

    [minVal, maxVal, minLoc, maxLoc] = cv2.minMaxLoc(blur)
    # print minVal, maxVal, minLoc, maxLoc

    # Threshold at 80%
    margin = THRESHOLD_PERCENT
    thresh = int(maxVal * margin)
    # print "Threshold: %f" % thresh

    ret, thresh_img = cv2.threshold(blur, thresh, 255, cv2.THRESH_BINARY)

    cv2.imshow('TrashImage', thresh_img)

    image, contours, hierarchy = cv2.findContours(thresh_img, cv2.RETR_LIST , cv2.CHAIN_APPROX_NONE)

    curr_lights = []

    lights_pairs = []
    founded_pairs_for_previous_lights = [False] * len(prev_lights)

    new_lights = []

    for c in contours:
        area = cv2.contourArea(c)
        if (area >= MIN_AREA and area <= MAX_AREA):
            light = Light(c)
            curr_lights.append(light)

            # find pair
            pair_for_current_is_founded = False

            for prev_id, prev in enumerate(prev_lights):
                distance = light.distance(prev)
                # print "distance: {}".format(distance)
                if (distance < 120):
                    light.color = prev.color
                    lights_pairs.append([prev, light])
                    pair_for_current_is_founded = True
                    founded_pairs_for_previous_lights[prev_id] = True
                    break

            if not pair_for_current_is_founded:
                new_lights.append(light)

            x, y, w, h = cv2.boundingRect(c)
            cv2.rectangle(frame, (x, y), (x + w, y + h), light.color, 3)
            #cv2.circle(frame, (int(light.mass_center[0]), int(light.mass_center[1])), 1, CIRCLE_COLOR, 1)

    #lost_lights = []
    #for idx, val in enumerate(founded_pairs_for_previous_lights):
    #    if (val == False):
    #        lost_lights.append(prev_lights[idx])

    prev_lights = curr_lights

    message("Frame size: {} x {}".format(width, height), (10, 20), frame)
    message("Numbers of lights: {}".format(len(curr_lights)), (10, 35), frame)
    end = time.clock()
    framecost = end-start
    message("Frame cost, ms: {}".format(framecost), (10, 50), frame)
    start = time.clock();

    cv2.imshow('FrameImage', frame)
    #cv2.imshow('blurred', blur)

    #cv2.imshow('grayscale', gray)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()