import math

import numpy as np
import cv2


# import fxchanger
from vector import Vector
import time


MAX_VALUE = 9999999999999

MIN_AREA = 50
MAX_AREA = 5000
RECTANGLE_COLOR = (0, 255, 0)
CIRCLE_COLOR = (255, 0, 0)
THRESHOLD_PERCENT = 0.7
FONT = cv2.FONT_HERSHEY_SIMPLEX

SPEED_THRESHOLD = 100  # pixels per second

ATTACK_SPEED_A = 0.025
DECAY_DECREMENT_A = 0.025
ATTACK_SPEED_B = 0.05
DECAY_DECREMENT_B = 0.04
# ATTACK_SPEED_C = 0.1
# DECAY_DECREMENT_C = 0.2

cap = cv2.VideoCapture(0)

# wont work for realtime video
# fps = cap.get(cv2.CAP_PROP_FPS)
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


class Plot:
    def __init__(self, x, y, w, h):
        self.x = x
        self.y = y
        self.w = w
        self.h = h

    def draw(self, img, A, B, C):
        # cv2.fillConvexPoly(img, np.array(
        # [[self.x, self.y],
        # [self.x + self.w, self.y],
        # [self.x + self.w, self.y + self.h],
        # [self.x, self.y + self.h]], np.int32), (200, 200, 200))

        dW = self.w / 4
        dH = self.h / 2
        r = min(self.w, self.h) / 3

        cv2.circle(img, (int(self.x + dW), int(self.y + dH)), int(r), (255, 255, 255), 1)
        cv2.circle(img, (int(self.x + dW), int(self.y + dH)), int(A * r), (127, 127 + 20, 127 + 50), cv2.FILLED)

        cv2.circle(img, (int(self.x + dW * 2), int(self.y + dH)), int(r), (255, 255, 255), 1)
        cv2.circle(img, (int(self.x + dW * 2), int(self.y + dH)), int(B * r), (127, 127 + 50, 127 + 20), cv2.FILLED)

        cv2.circle(img, (int(self.x + dW * 3), int(self.y + dH)), int(r), (255, 255, 255), 1)
        cv2.circle(img, (int(self.x + dW * 3), int(self.y + dH)), int(C * r), (127 + 50, 127, 127 + 20), cv2.FILLED)

        # cv2.ellipse(img, (int(self.x + dW), int(self.y + dH)), (int(r), int(r)), 20, 0, int(360 * A),
        # (127, 127 + 20, 127 + 50), cv2.FILLED)
        #
        # cv2.ellipse(img, (int(self.x + dW), int(self.y + dH)), (int(r), int(r)), 0, 0, 360, (0, 0, 0), 1)
        #
        # cv2.ellipse(img, (int(self.x + dW * 2), int(self.y + dH)), (int(r), int(r)), 20, 0, int(360 * B),
        # (127, 127 + 50, 127 + 20), cv2.FILLED)
        #
        # cv2.ellipse(img, (int(self.x + dW * 2), int(self.y + dH)), (int(r), int(r)), 0, 0, 360, (0, 0, 0), 1)
        #
        # cv2.ellipse(img, (int(self.x + dW * 3), int(self.y + dH)), (int(r), int(r)), 20, 0, int(360 * C),
        # (127 + 50, 127, 127 + 20), cv2.FILLED)
        #
        # cv2.ellipse(img, (int(self.x + dW * 3), int(self.y + dH)), (int(r), int(r)), 0, 0, 360, (0, 0, 0), 1)


pl = Plot(0, height - 120, width, 120)


class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y


class Vector2:
    def __init__(self, start, end):
        self.start = start
        self.end = end

    def len(self):
        return calc_distance(self.start, self.end)


class Light:
    def __init__(self, contour, color):
        center, radius = cv2.minEnclosingCircle(contour)

        # moments = cv2.moments(contour, False)
        # self.mc = [moments['m10'] / moments['m00'], moments['m01'] / moments['m00']]
        self.contour = contour
        self.color = color
        self.dT = 0
        self.radius = radius
        self.center = Point(center[0], center[1])
        self.prev = None
        self.born = time.time()

    def distance(self, other):
        return Vector2(self.center, other.center).len()

    def set_previous(self, dT, prev):
        self.color = prev.color
        self.prev = prev
        self.born = prev.born
        self.dT = dT

    def vec(self):
        if self.prev == None:
            return Vector2(self.center, self.center)
        else:
            return Vector2(prev.center, self.center)

    def speed(self):
        if self.prev == None:
            return 0
        else:
            if self.dT == 0:
                return 0
            else:
                return self.vec().len() / self.dT

    MATURITY_TIME = 0.2

    def is_significant(self):
        return self.speed() > SPEED_THRESHOLD and ((time.time() - self.born) > self.MATURITY_TIME)


class FxModulator:
    def __init__(self):
        self.accumulated_A = 0
        self.accumulated_B = 0

    def modulate(self, lights_list):

        summ_velocity = Vector(0, 0)
        summ_length = 0
        for light in lights_list:
            start_point = light.vec().start
            end_point = light.vec().end
            velocity = Vector(end_point.x, end_point.y) - Vector(start_point.x, start_point.y)
            if (not light.is_significant()):
                continue

            summ_velocity += velocity
            summ_length += velocity.norm()

        summ_vel_magnitude = summ_velocity.norm()


        # some kind of velocity coherence


        # C - fast moving fx (period should be about 0.5..1s)
        if summ_length > 0:
            coherence = summ_vel_magnitude / summ_length  # should be in range 0..1
            self.accumulated_C = coherence
        else:
            coherence = 0
            self.accumulated_C = 0


        # A - very slow moving fx (period should be about 10 sec)
        self.accumulated_A += self.accumulated_C * ATTACK_SPEED_A
        self.accumulated_A -= DECAY_DECREMENT_A

        # B - middle-speed moving fx (period should be about 5 sec)
        self.accumulated_B += self.accumulated_C * ATTACK_SPEED_B
        self.accumulated_B -= DECAY_DECREMENT_B

        self.accumulated_A = np.clip(self.accumulated_A, 0, 1.0)
        self.accumulated_B = np.clip(self.accumulated_B, 0, 1.0)
        self.accumulated_C = np.clip(self.accumulated_C, 0, 1.0)

        print("ABC=", self.accumulated_A, self.accumulated_B, self.accumulated_C)

        return self.accumulated_A, self.accumulated_B, self.accumulated_C


prev_lights = []

# Failed under Windows 8
# fx_changer = fxchanger.FxChanger()
modulator = FxModulator()

start_time = time.time() - 30  # pretend we have started earlier

while (cap.isOpened()):
    # time.sleep(0.005)
    end_time = time.time()
    dT = end_time - start_time
    start_time = end_time

    brightness = cap.get(cv2.CAP_PROP_BRIGHTNESS)
    ret, frame = cap.read()

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    blur = cv2.medianBlur(gray, 15)
    # cv2.imshow('Blured', blur)

    # blur = cv2.GaussianBlur(gray, (7, 7), 8)

    [minVal, maxVal, minLoc, maxLoc] = cv2.minMaxLoc(gray)

    margin = THRESHOLD_PERCENT
    thresh = np.clip(int(maxVal * margin), 48, 255)
    # print "Threshold: %f" % thresh

    ret, thresh_img = cv2.threshold(blur, thresh, 255, cv2.THRESH_BINARY)
    cv2.imshow('Threshold', thresh_img)

    image, contours, hierarchy = cv2.findContours(thresh_img, cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)

    curr_lights = []

    new_lights = []
    founded_pairs_for_previous_lights = [False] * len(prev_lights)

    for c in contours:
        area = cv2.contourArea(c)
        if (area >= MIN_AREA and area <= MAX_AREA):
            light = Light(c, rnd_color())
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
                    light.set_previous(dT, prev)

                    dX = light.center.x - prev.center.x
                    dY = light.center.y - prev.center.y

                    if (light.is_significant()):
                        cv2.arrowedLine(frame,
                                        (int(prev.center.x + dX), int(prev.center.y + dY)),
                                        (int(light.center.x + dX * 2), int(light.center.y + dY * 2)),
                                        RECTANGLE_COLOR, 2)

            if (light.is_significant()):
                x, y, w, h = cv2.boundingRect(c)
                # center, radius = cv2.minEnclosingCircle(c)
                # cv2.circle(frame, (int(center[0]),int(center[1])), int(radius), CIRCLE_COLOR, 2);
                cv2.rectangle(frame, (x - 5, y - 5), (x + w + 5, y + h + 5), light.color, 2)
                cv2.circle(frame, (int(light.center.x), int(light.center.y)), 2, CIRCLE_COLOR, 1)

    # lost_lights = []
    # for idx, val in enumerate(founded_pairs_for_previous_lights):
    # if (val == False):
    # lost_lights.append(prev_lights[idx])

    # print("light speeds:")
    # for l in curr_lights:
    # print l.speed()

    prev_lights = curr_lights

    A, B, C = modulator.modulate(curr_lights)

    # Failed under Windows 8
    # fx_changer.set(FxChanger.FX_ID.A, A)
    # fx_changer.set(FxChanger.FX_ID.B, B)
    # fx_changer.set(FxChanger.FX_ID.C, C)


    # cv2.imshow('TrashImage', thresh_img)
    # cv2.imshow('GrayImage', gray)

    fps = 1.0 / dT
    message(
        "Frame size: {} x {}. Fps: {}. Brightness: {}. DistanceC: {}"
            .format(width, height, fps, brightness, distance_coefficient), (10, 20), frame)

    message("Frame dT, ms: {}".format((dT) * 1000), (10, 50), frame)

    message("Numbers of lights: {}".format(len(curr_lights)), (10, 35), frame)

    pl.draw(frame, A, B, C)
    cv2.imshow('Captured', frame)

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