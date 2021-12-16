from datetime import datetime, time
import math
import os
from collections import deque
import numpy as np
import cv2
import imutils
from imutils.video import FPS
import time
import tkinter as tk
import tkinter.ttk as ttk
import PIL.Image
import PIL.ImageTk


class ComputerVision:
    def __init__(self, _buffer=64):
        self.isHeld = False
        self.buffer = _buffer

        # data set to default
        self.detectedObject = False
        self.numObjects = 0

        #changed to a deque
        self.targetData = deque(maxlen=self.buffer)

        #self.targetData = [None] * 3
        self.interceptData = [None] * 3
        self.speed = None
        self.start_time = time.time_ns()

        # Lists for tracked points and times
        self.pts = deque(maxlen=self.buffer)
        self.pts_times = deque(maxlen=self.buffer)
        self.pred_pts = deque(maxlen=self.buffer)
        self.rpred = deque(maxlen=self.buffer)
        self.pred_pts_times = deque(maxlen=self.buffer)

        # predict flag
        self.predicted = False

    #def setup_trackbars(self, range_filter, colorLower=None, colorUpper=None):
    #    cv2.namedWindow("Trackbars", 0)

    #    # if there are saved tracking values use them else use min and max
    #    if colorLower is None and colorUpper is None:
    #        for i in ["MIN", "MAX"]:
    #            v = 0 if i == "MIN" else 255

    #            for j in range_filter:
    #                cv2.createTrackbar("%s_%s" % (j, i), "Trackbars", v, 255, callback)
    #    else:
    #        for i in ["MIN", "MAX"]:
    #            if i == "MIN":
    #                v = colorLower
    #            else:
    #                v = colorUpper

    #            for j in range_filter:
    #                if j == 'H':
    #                    num = 0
    #                elif j == 'S':
    #                    num = 1
    #                else:
    #                    num = 2
    #                cv2.createTrackbar("%s_%s" % (j, i), "Trackbars", v[num], 255, callback)

    #def get_trackbar_values(self, range_filter,):
    #    values = []
    #    # Get the current positions of each bar and append them to lists
    #    for i in ["MIN", "MAX"]:
    #        for j in range_filter:
    #            v = cv2.getTrackbarPos("%s_%s" % (j, i), "Trackbars")
    #            values.append(v)

    #    return values



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
                #c = max(cnts, key=cv2.contourArea)
                ((x, y), radius) = cv2.minEnclosingCircle(c)
                M = cv2.moments(c)
                center = (int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"]))

            # only proceed if radius meets the required size
                if radius > 4:
                    objects = [None] * 3
                    objects[0] = int(x)
                    objects[1] = int(y)
                    objects[2] = int(radius)
                    #self.targetData[0] = int(x)
                    #self.targetData[1] = int(y)
                    #self.targetData[2] = int(radius)
                    self.targetData.appendleft(objects)
                    self.__Detected(True)

        # update the points queue None is used to remove queue points
        self.pts.appendleft(center)

        # if no object is detected drop detected flag and remove target data
        if center is None:
            self.pts_times.appendleft(None)
            self.__Detected(False)
            self.__Predicted(False)
            #self.targetData = [None] * 3
            self.targetData.appendleft(None)
        else:
            self.pts_times.appendleft((time.time_ns() - self.start_time)) # time is recorded in xtime (since epoch) using start time to get smaller usable numbers
        
        # adjust predict if target is lost
        if not self.isDetected():
            self.__Predicted(False)

    def predict(self, delay):
        # Determine if it is meeting the predicted points. If it isn't assume it is held
        if not self.isHeld:
            if self.pred_pts is not None and len(self.pred_pts) != 0:
                if self.targetData[0][0] != self.pred_pts[len(self.pred_pts) - 1][0] and self.targetData[0][1] != self.pred_pts[len(self.pred_pts) - 1][1]:
                    self.isHeld = True
        else:
            if self.pred_pts is not None and len(self.pred_pts) != 0:
                count = 0
                for i in range(0,4):
                    if self.pts[i] is not None and self.pred_pts[i] is not None:
                        if self.pts[i][0] == self.pred_pts[i][0] and self.pts[i][1] == self.pred_pts[i][1]:
                            count += 1
                if count > 3:
                    self.isHeld = False

        for i in range(5):
            if self.pts_times[i] is None:
                return
        # default args
        gravity = 9.801
        nano_sec_conv = 1000000000 # convertion variable for nanoseconds in a second

        time_avg = (self.pts_times[0] - self.pts_times[4]) / nano_sec_conv
        t = (self.pts_times[0] / nano_sec_conv) # will be used later for intercept aiming

        x1, y1 = self.__extrapolate(self.targetData[0][0], self.targetData[0][1]) # points on the camera grid
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
        if self.isHeld:
            self.interceptData[0] = self.targetData[0][0]
            self.interceptData[1] = self.targetData[0][1]
            self.interceptData[2] = self.pred_pts_times[1]
        else:
            for i in range(len(self.pred_pts)):
                if (self.pred_pts_times[i] - delay) > 0:
                    self.interceptData[0] = self.pred_pts[i][0]
                    self.interceptData[1] = self.pred_pts[i][1]
                    self.interceptData[2] = self.pred_pts_times[i]
        self.__Predicted(True)
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
        return self.predicted

    def __Predicted(self, flag):
        self.predicted = flag

    def __extrapolate(self, x, y):
        rx = (x / 400) * 0.3
        ry = (y / 300) * 0.3
        return rx, ry

    def __pt_convert(self, rx, ry):
        x = (rx / 0.3) * 400
        y = (ry / 0.3) * 300
        return x, y

    def clear_targetData(self):
        self.targetData = deque(maxlen=self.buffer)


# class peopleDetect:
#     def __init__(self):
#         # paths to the Caffe prototxt file and the pretrained model
#         prototxt = 'nets/deploy.prototxt'
#         model = 'nets/mobilenet_iter_73000'
#
#         # initialize the list of class labels MobileNet SSD was trained to
#         # detect, then generate a set of bounding box colors for each class
#         self.CLASSES = ["background", "aeroplane", "bicycle", "bird", "boat",
#                    "bottle", "bus", "car", "cat", "chair", "cow", "diningtable",
#                    "dog", "horse", "motorbike", "person", "pottedplant", "sheep",
#                    "sofa", "train", "tvmonitor"]
#         self.COLORS = np.random.uniform(0, 255, size=(len(self.CLASSES), 3))
#
#         # load our serialized model from disk
#         print("[INFO] loading model...")
#         self.net = cv2.dnn.readNetFromCaffe(prototxt, model)
#
#     def detect(self, frame):
#         (h, w) = frame.shape[:2]
#         blob = cv2.dnn.blobFromImage(cv2.resize(frame, (300, 300)), 0.007843,
#                                      (300, 300), 127.5)
#
#         # pass the blob through the network and obtain the detections and
#         # predictions
#         print("[INFO] computing object detections...")
#         self.net.setInput(blob)
#         detections = self.net.forward()
#
#         # loop over the detections
#         for i in np.arange(0, detections.shape[2]):
#             # extract the confidence (i.e., probability) associated with the
#             # prediction
#             confidence = detections[0, 0, i, 2]
#             # filter out weak detections by ensuring the `confidence` is
#             # greater than the minimum confidence
#             if confidence > 0.7:
#                 # extract the index of the class label from the `detections`,
#                 # then compute the (x, y)-coordinates of the bounding box for
#                 # the object
#                 idx = int(detections[0, 0, i, 1])
#                 box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
#                 (startX, startY, endX, endY) = box.astype("int")
#                 # display the prediction
#                 label = "{}: {:.2f}%".format(self.CLASSES[idx], confidence * 100)
#                 print("[INFO] {}".format(label))
#                 cv2.rectangle(frame, (startX, startY), (endX, endY),
#                               self.COLORS[idx], 2)
#                 y = startY - 15 if startY - 15 > 15 else startY + 15
#                 cv2.putText(frame, label, (startX, y),
#                             cv2.FONT_HERSHEY_SIMPLEX, 0.5, self.COLORS[idx], 2)
#
#         return frame


def callback(value):
    pass

class HSVRange:
        def __init__(self, _vs, colorLower=[0,0,0], colorUpper=[255,255,255]):
            # Return equivilent
            self.__running = True
            self.lower = None
            self.upper = None

            # Create video variable
            self.vs = _vs

            # set hsv variables
            self.v1_min = int(colorLower[0])
            self.v2_min = int(colorLower[1])
            self.v3_min = int(colorLower[2])
            self.v1_max = int(colorUpper[0])
            self.v2_max = int(colorUpper[1])
            self.v3_max = int(colorUpper[2])
            
            # Create Window
            self.window = tk.Toplevel()

            # Create frame for regular image
            self.window['bg'] = "#628395"
            self.window.title('Target Practice')
            self.window.iconbitmap('Art/Tpp-logo-vertical.ico')

            # Create a canvases that can fit the video source size
            self.vid_canvases = tk.Canvas(self.window, width=400, height=600, bg="#628395")
            self.reg_canvas = tk.Canvas(self.vid_canvases, width=400, height=300, bg="#628395")
            self.thresh_canvas = tk.Canvas(self.vid_canvases, width=400, height=300, bg="#628395")

            # Create a canvas to hold sliders
            self.slider_canvas = tk.Canvas(self.window, width=400, height=300, bg="#628395")

            # Create HSV Sliders
            self.slider_v1_min = ttk.Scale(self.slider_canvas, from_=0, to=255, orient=tk.HORIZONTAL, length=256, command=self.slide)
            self.slider_v2_min = ttk.Scale(self.slider_canvas, from_=0, to=255, orient=tk.HORIZONTAL, length=256, command=self.slide)
            self.slider_v3_min = ttk.Scale(self.slider_canvas, from_=0, to=255, orient=tk.HORIZONTAL, length=256, command=self.slide)
            self.slider_v1_max = ttk.Scale(self.slider_canvas, from_=0, to=255, orient=tk.HORIZONTAL, length=256, command=self.slide)
            self.slider_v2_max = ttk.Scale(self.slider_canvas, from_=0, to=255, orient=tk.HORIZONTAL, length=256, command=self.slide)
            self.slider_v3_max = ttk.Scale(self.slider_canvas, from_=0, to=255, orient=tk.HORIZONTAL, length=256, command=self.slide)

            # set sliders to value
            self.slider_v1_min.config(value=self.v1_min)
            self.slider_v2_min.config(value=self.v2_min)
            self.slider_v3_min.config(value=self.v3_min)
            self.slider_v1_max.config(value=self.v1_max)
            self.slider_v2_max.config(value=self.v2_max)
            self.slider_v3_max.config(value=self.v3_max)

            # Create apply button
            self.apply = tk.Button(self.window, text='Apply', command=self.done)
            
            # Place Canvases
            self.vid_canvases.grid(padx=5, pady=5, row=0, column=0)
            self.slider_canvas.grid(padx=5, pady=5, row=0, column=1)
            
            # Place Apply Button
            self.apply.grid(padx=15, pady=15, row=1, column=1)

            # Place video canvases
            self.reg_canvas.pack()
            self.thresh_canvas.pack()

            # Place sliders
            self.slider_v1_min.pack()
            self.slider_v2_min.pack()
            self.slider_v3_min.pack()
            self.slider_v1_max.pack()
            self.slider_v2_max.pack()
            self.slider_v3_max.pack()

            # set delay and initialize updating
            self.delay = 15
            self.update()

            # start the main infinite loop for the window
            self.window.mainloop()

        def update(self):
            # Get next video frame
            ret, frame = self.vs.get_frame()

            # resize the image
            image = imutils.resize(frame, width=400)

            if ret:
                frame_to_thresh = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
                
                # Set a frame to show only the HSV(Color adjusted) image
                thresh = cv2.inRange(frame_to_thresh, (self.v1_min, self.v2_min, self.v3_min), (self.v1_max, self.v2_max, self.v3_max))

                # Place frames in the canvases
                self.img_frame = PIL.ImageTk.PhotoImage(image=PIL.Image.fromarray(image))
                self.thresh_frame = PIL.ImageTk.PhotoImage(image=PIL.Image.fromarray(thresh))
                self.reg_canvas.create_image(0, 0, image=self.img_frame, anchor=tk.NW)
                self.thresh_canvas.create_image(0, 0, image=self.thresh_frame, anchor=tk.NW)

            # ensure continual updates
            self.window.after(self.delay, self.update)
                
        def done(self):
            # save settings
            settings = np.array([self.v1_min, self.v2_min, self.v3_min]), np.array([self.v1_max, self.v2_max, self.v3_max])
            if not os.path.isdir('data'):
                os.mkdir('data')
            np.savetxt('data/settings.csv', settings, delimiter=',')

            self.lower = np.array([self.v1_min, self.v2_min, self.v3_min])
            self.upper = np.array([self.v1_max, self.v2_max, self.v3_max])
            self.__running = False

            self.window.destroy()

        def isRunning(self):
            return self.__running

        def setRunning(self, _bool):
            self.__running = _bool

        def slide(self, x):
            self.v1_min = int(self.slider_v1_min.get())
            self.v2_min = int(self.slider_v2_min.get())
            self.v3_min = int(self.slider_v3_min.get())
            self.v1_max = int(self.slider_v1_max.get())
            self.v2_max = int(self.slider_v2_max.get())
            self.v3_max = int(self.slider_v3_max.get())

        def getLower(self):
            return self.lower

        def getUpper(self):
            return self.upper
