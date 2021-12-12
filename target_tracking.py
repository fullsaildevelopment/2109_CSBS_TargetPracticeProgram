import math
import os
from collections import deque
import numpy as np
import cv2
import imutils
import time


class ComputerVision:
    def __init__(self, _buffer=64):
        self.predicted_object = False
        self.buffer = _buffer

        # data set to default
        self.detectedObject = False
        self.numObjects = 0

        #changed to a deque
        #Stuff for git hub
        #Multi Object
        #self.targetData = deque(maxlen=self.buffer)
        #single object
        self.targetData = [None] * 3
        self.interceptData = [None] * 3
        self.speed = None
        self.start_time = time.time_ns()
        

        # define the lower and upper boundaries of the ball color
        # ball in the HSV color space, then initialize the
        # list of tracked points
        self.pts = deque(maxlen=self.buffer)
        self.pts_times = deque(maxlen=self.buffer)
        self.pred_pts = deque(maxlen=self.buffer)
        self.rpred = deque(maxlen=self.buffer)
        self.pred_pts_times = deque(maxlen=self.buffer)

        # Kalman Filter
        self.kf = cv2.KalmanFilter(4, 2)
        self.kf.measurementMatrix = np.array([[1, 0, 0, 0], [0, 1, 0, 0]], np.float32)
        self.kf.transitionMatrix = np.array([[1, 0, 1, 0], [0, 1, 0, 1], [0, 0, 1, 0], [0, 0, 0, 1]], np.float32)

    def setup_trackbars(self, range_filter):
        cv2.namedWindow("Trackbars", 0)

        for i in ["MIN", "MAX"]:
            v = 0 if i == "MIN" else 255

            for j in range_filter:
                cv2.createTrackbar("%s_%s" % (j, i), "Trackbars", v, 255, callback)

    def get_trackbar_values(self, range_filter):
        values = []

        for i in ["MIN", "MAX"]:
            for j in range_filter:
                v = cv2.getTrackbarPos("%s_%s" % (j, i), "Trackbars")
                values.append(v)

        return values

    def HSVRange(self, vs):
        self.setup_trackbars('HSV')

        while True:
            ret, image = vs.get_frame()

            frame_to_thresh = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

            v1_min, v2_min, v3_min, v1_max, v2_max, v3_max = self.get_trackbar_values('HSV')

            thresh = cv2.inRange(frame_to_thresh, (v1_min, v2_min, v3_min), (v1_max, v2_max, v3_max))         
            

            cv2.imshow("Original", image)
            cv2.imshow("Thresh", thresh)

            if cv2.waitKey(1) & 0xFF is ord('q'):
                break

        # close all windows
        cv2.destroyAllWindows()

        # save settings
        settings = np.array([v1_min, v2_min, v3_min]), np.array([v1_max, v2_max, v3_max])
        if not os.path.isdir('data'):
            os.mkdir('data')
        np.savetxt('data/settings.csv', settings, delimiter=',')

        return np.array([v1_min, v2_min, v3_min]), np.array([v1_max, v2_max, v3_max])

    def detect(self, mask):
        # find contours in the mask and initialize the current
        # (x, y) center of the ball
        cnts = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL,
                                cv2.CHAIN_APPROX_SIMPLE)
        cnts = imutils.grab_contours(cnts)
        center = None
        
        # only proceed if at least one contour was found
        if len(cnts) > 0:
            # find the largest contour in the mask, then use
            # it to compute the minimum enclosing circle and
            # centroid
            for c in cnts:
                #***comment out next line only for multi object***
                c = max(cnts, key=cv2.contourArea)
                ((x, y), radius) = cv2.minEnclosingCircle(c)
                M = cv2.moments(c)
                center = (int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"]))

            # only proceed if radius meets the required size
                if radius > 4:
                    objects = [None] * 3
                    objects[0] = int(x)
                    objects[1] = int(y)
                    objects[2] = int(radius)
                    #***single object***
                    self.targetData[0] = int(x)
                    self.targetData[1] = int(y)
                    self.targetData[2] = int(radius)
                    #****multi object***
                    #self.targetData.appendleft(objects)
                    self.__Detected(True)

        # update the points queue None is used to remove queue points
        self.pts.appendleft(center)

        # if no object is detected drop detected flag and remove target data
        if center is None:
            self.pts_times.appendleft(None)
            self.__Detected(False)
            self.__Predicted(False)
            #***single object detect with largest radius***
            self.targetData = [None] * 3
            #***muli objcet detect***
            #self.targetData.appendleft(None)
        else:
            self.pts_times.appendleft((time.time_ns() - self.start_time)) # time is recorded in xtime (since epoch) using start time to get smaller usable numbers

    def predict(self, delay):
        for i in range(5):
            if self.pts_times[i] is None:
                return
        # default args
        gravity = 9.801
        nano_sec_conv = 1000000000 # convertion variable for nanoseconds in a second

        time_avg = (self.pts_times[0] - self.pts_times[4]) / nano_sec_conv
        t = (self.pts_times[0] / nano_sec_conv) # will be used later for intercept aiming

        #Single Object
        x1, y1 = self.__extrapolate(self.targetData[0], self.targetData[1]) # points on the camera grid
        #Multi Object
        #x1, y1 = self.__extrapolate(self.targetData[0][0], self.targetData[0][1]) # points on the camera grid
        x4, y4 = self.__extrapolate(self.pts[4][0], self.pts[4][1])

        # distance both vertically and horizontaly traveled over the latest 4 point
        x_dist = x1 - x4
        y_dist = y1 - y4

        # coefficient calculation velocity and time taken to travel between points
        x_vel = x_dist / time_avg
        y_vel = y_dist / time_avg
        self.speed = math.sqrt(pow(x_vel, 2) + pow(y_vel, 2))
        time_delta = 0.005

        for i in range(1, self.buffer):
            # predict positions
            next_time = t + time_delta
            next_x = x1 + x_vel * time_delta
            next_y = y1 + y_vel * time_delta + 0.5 * gravity * pow(time_delta, 2)

            # add predicted camera position to array and extrapolate real world position
            prediction = np.array(np.float32(next_x), np.float32(next_y))
            rx, ry = self.__pt_convert(next_x, next_y)
            rpred = np.array([int(rx), int(ry)])
            self.rpred.appendleft(prediction)
            self.pred_pts.appendleft(rpred)
            self.pred_pts_times.appendleft(next_time)

            # update variables for next points to be predicted.
            x1 = next_x
            y1 = next_y
            y_vel = y_vel + gravity * time_delta
            t = next_time

        # select a intercept point that the counter_measure device can reach before the target
        for i in range(len(self.pred_pts)):
            if (self.pred_pts_times[i] - delay) > 0:
                self.interceptData[0] = self.pred_pts[i][0]
                self.interceptData[1] = self.pred_pts[i][1]
                self.interceptData[2] = self.pred_pts_times[i]
        return self.interceptData

    def get_targetData(self):
        return self.targetData

    def __set_targetData(self, x, y, radius):
        self.targetData[0] = x
        self.targetData[1] = y
        self.targetData[2] = radius

    def get_interceptData(self):
        return self.interceptData

    def __set_interceptData(self, data):
        self.interceptData = data

    def get_numObjects(self):
        return self.numObjects

    def __set_numObjects(self, data):
        self.numObjects = data

    def isDetected(self):
        return self.detectedObject

    def __Detected(self, flag):
        self.detectedObject = flag
        if flag:
            self.start_time = time.time()

    def CleanUp(self, frame, colorLower, colorUpper):
        # values here are based on my current camera capture
        frame = imutils.resize(frame, width=400)
        blurred = cv2.GaussianBlur(frame, (11, 11), 0)
        hsv = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)

        mask = cv2.inRange(hsv, colorLower, colorUpper)
        mask = cv2.erode(mask, None, iterations=2)
        mask = cv2.dilate(mask, None, iterations=2)

        return frame, mask

    def isPredicted(self):
        return self.predicted_object

    def __Predicted(self, flag):
        self.predicted_object = flag

    def __extrapolate(self, x, y):
        rx = (x / 400) * 0.3
        ry = (y / 300) * 0.3
        return rx, ry

    def __pt_convert(self, rx, ry):
        x = (rx / 0.3) * 400
        y = (ry / 0.3) * 300
        return x, y

def callback(value):
    pass
