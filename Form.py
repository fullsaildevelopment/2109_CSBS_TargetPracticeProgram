import datetime
import os
import tkinter as tk
from collections import deque

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
        self.aim = counter_measure.AimingCalc()
        # People Detector
        #self.peopleD = target_tracking.peopleDetect()


        # calibrate counter_measure device
        self.aim.set_delay()

        # Create initial window
        self.root = tk.Tk()
        self.root.title('Target Practice')
        #self.root.iconbitmap('Art/Tpp-logo-horizontal.bmp')

        # video source
        self.video_source = video_source
        self.vid = MyVideoCapture(self.video_source)

        # find upper and lower HSV value
        if not (os.path.exists(set_filename)):
            self.colorLower, self.colorUpper = self.cv.HSVRange(self.vid)
        else:
            self.colorLower, self.colorUpper = np.loadtxt(set_filename, delimiter=',', dtype=int)

        # Create a canvases that can fit the above video source size
        self.canvas = tk.Canvas(self.root, width=400, height=300)
        self.info_canvas = tk.Canvas(self.root, width=15, height=300)

        # Create side info window
        self.tracking_text = tk.StringVar()
        self.text_box = tk.Label(self.info_canvas, bg="green", textvariable=self.tracking_text, width=15, height=5)

        # Create readout window
        self.read_out = tk.Text(self.info_canvas, bg="white", width=15, height=13)
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
               self.intercept = self.cv.predict(self.aim.get_delay())
               self.cv.numObjects = 2
        # Get a frame from the video source
        ret, frame = self.vid.get_frame()

        if not ret:
            print("No Video Source Retrieved")
            return -1

        # Find People
        #frame = self.peopleD.detect(frame)

        # clean the frame to see just the target size of frame is 400x300pts
        frame, mask = self.cv.CleanUp(frame, self.colorLower, self.colorUpper)

        
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
                cv2.circle(frame, (self.cv.targetData[i][0], self.cv.targetData[i][1]), self.cv.targetData[i][2], [255, 0, 0], 2)

        if len(self.cv.pred_pts) > 0 and self.cv.targetData[0] is not None:
            for i in range(len(self.cv.pred_pts)):
                if self.cv.pred_pts[i] is None:
                    continue
                # draw prediction circle
                color = [114, 42, 203]
                if self.intercept is not None:
                    if self.intercept[0] == self.cv.pred_pts[i][0] and self.intercept[1] == self.cv.pred_pts[i][1]:
                        color = [0, 255, 0]
                    
                cv2.circle(frame, (self.cv.pred_pts[i][0], self.cv.pred_pts[i][1]), (int(self.cv.targetData[0][2] / 2)), color, 2)
        if len(self.cv.pred_pts) > 0 and intercept is not None:  #CMM commands input(James)                  
                self.aim.cmmpitch(self.cv.interceptData[0]) 
                #self.aim.cmmpitch(self.cv.targetData[0][1])
                self.aim.cmmyaw(self.cv.interceptData[1])
                #self.aim.cmmyaw(self.cv.targetData[0][0])
                self.aim.cmmfire(self.cv.interceptData[2])
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