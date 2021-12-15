import datetime
import os
import tkinter as tk
from collections import deque
import math

import PIL.Image
import PIL.ImageTk
import cv2
import numpy as np

import SavesForm
import counter_measure
import target_tracking
import pyfirmata


class MyVideoCapture:
    def __init__(self, video_source=0):
        # Open the video source
        self.vid = cv2.VideoCapture(video_source)
        if not self.vid.isOpened():
            raise ValueError("Unable to open video source", video_source)

        # Get video source width and height
        self.width = self.vid.get(cv2.CAP_PROP_FRAME_WIDTH)
        self.height = self.vid.get(cv2.CAP_PROP_FRAME_HEIGHT)

    def get_frame(self, selected=None):
        # offset the capture to one frame before the desired frame before reading
        if selected is not None:
            if selected != 0:
                selected -= 1
            self.vid.set(cv2.CAP_PROP_POS_FRAMES, selected)
        if self.vid.isOpened():
            ret, frame = self.vid.read()
            if ret:
                # Return a boolean success flag and the current frame converted
                return (ret, cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            else:
                return (ret, None)
        else:
            return (None, None)

    # Release the video source when the object is destroyed
    def __del__(self):
        if self.vid.isOpened():
            self.vid.release()


class Form:
    def __init__(self, video_source=0):
        set_filename = 'data/settings.csv'
        buffer = 32

        # Points for safe box if drawn
        self.safe_pt1 = None
        self.safe_pt2 = None

        # Flag to show if user is still dragging
        self.isDragging = False

        # Define Intercept Point
        self.intercept = None

        # counter_measure thread
        #self.cmm_thread = None

        # save collections
        self.save_count = 0
        self.save_vid = deque(maxlen=(buffer*4))
        self.save_info = deque(maxlen=(buffer*4))

        # Target tracking
        self.cv = target_tracking.ComputerVision(_buffer=buffer)
        # Countermeasure Calibration
        #self.aim = counter_measure.AimingCalc()
        # People Detector
        #self.peopleD = target_tracking.peopleDetect()

        # Delay for predictions
        self.pred_delay = 5
        self.predict_count = 0

        # calibrate counter_measure device
        #self.aim.set_delay()

        # Create initial window
        self.root = tk.Tk()
        self.root['bg'] = "#628395"
        self.root.title('Target Practice')

        # Add Icon
        if not (os.path.exists(r'Art/Tpp-logo-vertical.ico')):
            fileico = r'Art/Tpp-logo-vertical.png'
            ico = PIL.Image.open(fileico)
            ico.save('Art/Tpp-logo-vertical.ico', format= 'ICO', sizes=[(32,32)])
        self.root.iconbitmap('Art/Tpp-logo-vertical.ico')

        # video source
        self.video_source = video_source
        self.vid = MyVideoCapture(self.video_source)

        # find upper and lower HSV value
        if not (os.path.exists(set_filename)):
            self.colorLower, self.colorUpper = self.cv.HSVRange(self.vid)
        else:
            self.colorLower, self.colorUpper = np.loadtxt(set_filename, delimiter=',', dtype=int)

        # Create a canvases that can fit the above video source size
        self.canvas = tk.Canvas(self.root, width=400, height=300, bg="#628395")
        self.info_canvas = tk.Canvas(self.root, width=15, height=300, bg="#628395")

        # Create side info window
        self.tracking_text = tk.StringVar()
        self.text_box = tk.Label(self.info_canvas, bg="#3EC300", textvariable=self.tracking_text, width=15, height=5)

        # Create readout window
        self.read_out = tk.Text(self.info_canvas, bg="#FCFCFC", width=15, height=13)
        self.read_out.config(state='disabled')

        # Save navigation
        self.menubar = tk.Menu(self.root)
        self.filemenu = tk.Menu(self.menubar, tearoff=0)
        self.filemenu.add_command(label="Saves", command=self.saves_launch)
        self.filemenu.add_command(label="Retrain", command=self.retrain)

        self.filemenu.add_separator()

        self.filemenu.add_command(label="Exit", command=self.root.quit)
        self.menubar.add_cascade(label="File", menu=self.filemenu)

        # Place widgets
        self.canvas.pack(padx=5, pady=5, side=tk.LEFT)
        self.text_box.grid(row=0, column=1, pady=5)
        self.read_out.grid(row=1, column=1, pady=5)
        self.info_canvas.pack(padx=5, pady=5, side=tk.LEFT)
        
        # Event for protected area initial click
        def safe_box_initial(event):
            x = event.x
            y = event.y
            # If outside of view box set to closest max
            if x > 400:
                x = 400
            if x < 0:
                x = 0
            if y > 300:
                y = 300
            if y < 0:
                y = 0
            self.safe_pt1 = (x,y)

        # While dragging continue updating the second point
        def safe_box_drag(event):
            x = event.x
            y = event.y
            # If outside of view box set to closest max
            if x > 400:
                x = 400
            if x < 0:
                x = 0
            if y > 300:
                y = 300
            if y < 0:
                y = 0
            self.isDragging = True
            self.safe_pt2 = (x,y)
        
        # Set flag stating box is set
        def safe_box_release(event):
            if self.safe_pt1 is not None and self.safe_pt2 is not None:
                # adjust points for safe zone so point 1 is top left and point 2 is bottom right
                if self.safe_pt1[0] > self.safe_pt2[0] or self.safe_pt1[1] > self.safe_pt2[1]:
                    hypotnuse_length = math.sqrt(((self.safe_pt2[0] - self.safe_pt1[0]) ** 2) + ((self.safe_pt2[1] - self.safe_pt1[1]) ** 2))
                    if self.safe_pt1[0] > self.safe_pt2[0]:
                        pt1_x = self.safe_pt2[0]
                        pt2_x = self.safe_pt1[0]
                    else:
                        pt1_x = self.safe_pt1[0]
                        pt2_x = self.safe_pt2[0]
                
                    if self.safe_pt1[1] > self.safe_pt2[1]:
                        pt1_y = self.safe_pt2[1]
                        pt2_y = self.safe_pt1[1]
                    else:
                        pt1_y = self.safe_pt1[1]
                        pt2_y = self.safe_pt2[1]
                    self.safe_pt1 = (pt1_x, pt1_y)
                    self.safe_pt2 = (pt2_x, pt2_y)
            self.isDragging = False

        # Right click menu
        rmenu = tk.Menu(self.root, tearoff=False)
        # menu items
        rmenu.add_command(label="Clear", command=self.clear_safe)
        # Right click command
        def right_menu(event):
            try:
                rmenu.tk_popup(event.x_root, event.y_root)
            finally:
                rmenu.grab_release()

        # Bind events to the canvas that displays the image
        self.canvas.bind("<ButtonPress-1>", safe_box_initial)
        self.canvas.bind("<B1-Motion>", safe_box_drag)
        self.canvas.bind("<ButtonRelease-1>", safe_box_release)
        self.canvas.bind("<Button-3>", right_menu)

        # Update will be called after every delay
        self.delay = 15
        self.update()

        self.root.config(menu=self.menubar)
        self.root.resizable(False, False)
        self.root.mainloop()

    def update(self):
        # Predict intercept point if it has enough info
        if self.cv.isDetected():
           if len(self.cv.pts) > 5 and self.cv.pts[0] is not None and self.cv.pts[1] is not None:
               # Only predict after a certain amount of delay if already predicted
               if not (self.cv.isPredicted()) or self.predict_count >= self.pred_delay:
                   self.predict_count = 0
                   self.intercept = self.cv.predict(1)#self.aim.get_delay())
                   self.cv.numObjects = 2
               else:
                   self.predict_count += 1

        # Get a frame from the video source
        ret, frame = self.vid.get_frame()

        if not ret:
            print("No Video Source Retrieved")
            return -1

        # Find People
        #frame = self.peopleD.detect(frame)

        # clean the frame to see just the target size of frame is 400x300pts
        frame, mask = self.cv.CleanUp(frame, self.colorLower, self.colorUpper)

        
        # Clear tracking data so it only shows one red circle for each target
        self.cv.clear_targetData()
        
        # Find the ball
        #for i in rage(0,self.cv.numObjects):               
        self.cv.detect(mask)
         

        # draw the tracked points as a line
        for i in range(1, len(self.cv.pts)):
            # Ignore None points
            if self.cv.pts[i - 1] is None or self.cv.pts[i] is None:
                continue
            # compute thickness based on place in queue
            thickness = int(np.sqrt(self.cv.buffer / float(i + 1)) * 2.5)
            # draw connecting lines between points
            cv2.line(frame, self.cv.pts[i - 1], self.cv.pts[i], (0, 0, 255), thickness)

        #if self.cv.targetData[0] is not None:
            # draw a circle around the target
        for i in range(len(self.cv.targetData)):
            if self.cv.targetData[i] is not None:
                cv2.circle(frame, (self.cv.targetData[i][0], self.cv.targetData[i][1]), self.cv.targetData[i][2], [221, 28, 26], 2)

        # Draw the safe square if selected
        if self.safe_pt1 is not None and self.safe_pt2 is not None:
            distance = math.sqrt(((self.safe_pt2[0] - self.safe_pt1[0]) ** 2) + ((self.safe_pt2[1] - self.safe_pt1[1]) ** 2))
            if self.isDragging or distance > 10:
                cv2.rectangle(frame, self.safe_pt1, self.safe_pt2, [16, 11, 0], 4)
                # if predicted intercept is not in the square remove it
                if self.intercept is not None:
                    if not ((self.intercept[0] >= self.safe_pt1[0] and self.intercept[1] >= self.safe_pt1[1]) and (self.intercept[0] <= self.safe_pt2[0] and self.intercept[1] <= self.safe_pt2[1])):
                        self.intercept = None
            else:
                self.safe_pt1 = None
                self.safe_pt2 = None

        if len(self.cv.pred_pts) > 0 and self.cv.targetData[0] is not None:
            for i in range(len(self.cv.pred_pts)):
                if self.cv.pred_pts[i] is None:
                    continue
                # draw prediction circle select color to green if it is the intercept point
                color = [255, 87, 10]
                if self.intercept is not None:
                    if self.intercept[0] == self.cv.pred_pts[i][0] and self.intercept[1] == self.cv.pred_pts[i][1]:
                        color = [62, 195, 0]
                if not self.cv.isHeld:
                    cv2.circle(frame, (self.cv.pred_pts[i][0], self.cv.pred_pts[i][1]), (int(self.cv.targetData[0][2] / 2)), color, 2)
                elif color == [62, 195, 0]:
                    cv2.circle(frame, (self.cv.pred_pts[i][0], self.cv.pred_pts[i][1]), (int(self.cv.targetData[0][2] / 2)), color, 2)

        
                
        #if len(self.cv.pred_pts) > 0 and intercept is not none:  #cmm commands input(james)
        #        self.aim.cmmpitch(self.cv.interceptdata[0]) 
        #        #self.aim.cmmpitch(self.cv.targetdata[0][1])
        #        self.aim.cmmyaw(self.cv.interceptdata[1])
        #        #self.aim.cmmyaw(self.cv.targetdata[0][0])
        #        self.aim.cmmfire(self.cv.interceptdata[2])

        # Place the next frame of the video into the window
        if ret:
            self.photo = PIL.ImageTk.PhotoImage(image=PIL.Image.fromarray(frame))
        self.canvas.create_image(0, 0, image=self.photo, anchor=tk.NW)

        # Set up the data on the target to display in the info box
        message = 'None Detected'
        if self.cv.isDetected():
            message = 'Detected:    1\n'
            message = message + 'Size:       ' + str(int(self.cv.targetData[0][2])) + '\n'
            if self.cv.speed is not None:
                message = message + 'Speed:    ' + str(round(self.cv.speed, 4)) + 'm/s'
                # collect information
                saveframe_info = np.array([1, int(self.cv.targetData[0][2]), round(self.cv.speed, 4)])
            else:
                saveframe_info = np.array([1, int(self.cv.targetData[0][2]), 0])

            # collect video frame
            self.save_vid.appendleft(frame)

            self.save_info.appendleft(saveframe_info)
            self.save_count = 0

        # Conditional save
        elif len(self.save_vid) > 32 and self.save_vid[0] is not None and self.save_count > 5:
            if not os.path.isdir('data/saves'):
                os.mkdir('data/saves')
            savefolder_name = 'data/saves/' + str(datetime.datetime.now()).replace(' ', '_')[0:-7].replace(':', '.')
            tsave = savefolder_name
            while os.path.isdir(savefolder_name):
                i = 0
                savefolder_name = tsave + '(' + str(i) + ')'
                i = i + 1
            os.mkdir(savefolder_name)
            save_name = savefolder_name + '/info.csv' # 'data/saves/2021-11-02_15.45.43/info.csv'
            np.savetxt(save_name, np.array(self.save_info, dtype='object'), delimiter=',', fmt='%s')
            save_name = savefolder_name + '/video.avi' # 'data/saves/2021-11-02_15.45.43/video.avi'
            fshape = frame.shape
            fheight = fshape[0]
            fwidth = fshape[1]
            fourcc = cv2.VideoWriter_fourcc(*'XVID')
            out = cv2.VideoWriter(save_name, fourcc, 20.0, (fwidth, fheight))
            for i in range(len(self.save_vid) - 1, -1, -1):
                if self.save_vid[i] is None:
                    continue
                out.write(self.save_vid[i])
                self.save_vid[i] = None
                self.save_info[i] = None
            out.release()

        # Update the number of saves
        self.save_count += 1

        # Set the info box for this frame
        self.tracking_text.set(message)

        self.root.after(self.delay, self.update)

    def saves_launch(self):
        SavesForm.SavesForm()

    def retrain(self):
        # Minimize the current window
        self.root.iconify()
        # remove the previous save data
        os.remove("data/settings.csv")
        # load up the Range setting loaded with current values
        self.colorLower, self.colorUpper = self.cv.HSVRange(self.vid, self.colorLower, self.colorUpper)
        # when closed bring the main window back up
        self.root.state(newstate='normal')

    def cmm_launch(self):
        self.cmm_thread = threading.Thread(target=counter_measure.AimingCalc)
        try:
            self.cmm_thread.start()
        except:
            print("Error: Unable to start cmm thread")

    def clear_safe(self):
        self.safe_pt1 = None
        self.safe_pt2 = None