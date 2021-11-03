import datetime
import os
import tkinter
from collections import deque
from tkinter import *
import PIL.Image, PIL.ImageTk
import cv2
import numpy as np
import threading
import SavesForm
import counter_measure
import target_tracking


class MyVideoCapture:
    def __init__(self, video_source=0):
        # Open the video source
        self.vid = cv2.VideoCapture(video_source)
        if not self.vid.isOpened():
            raise ValueError("Unable to open video source", video_source)

        # Get video source width and height
        self.width = self.vid.get(cv2.CAP_PROP_FRAME_WIDTH)
        self.height = self.vid.get(cv2.CAP_PROP_FRAME_HEIGHT)

    def get_frame(self):
        if self.vid.isOpened():
            ret, frame = self.vid.read()
            if ret:
                # Return a boolean success flag and the current frame converted to BGR
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

        # save thread
        self.save_thread = None

        # save collections
        self.save_vid = deque(maxlen=(buffer*4))
        self.save_info = deque(maxlen=(buffer*4))

        self.cv = target_tracking.ComputerVision(_buffer=buffer)
        self.aim = counter_measure.AimingCalc()

        # calibrate counter_measure device
        self.aim.set_delay()

        self.root = Tk()
        self.root.title('Target Practice')
        self.root.iconbitmap('Art/Tpp-logo-horizontal.bmp')

        # video source
        self.video_source = video_source
        self.vid = MyVideoCapture(self.video_source)

        # find upper and lower HSV value
        if not (os.path.exists(set_filename)):
            self.colorLower, self.colorUpper = self.cv.HSVRange(self.vid)
        else:
            self.colorLower, self.colorUpper = np.loadtxt(set_filename, delimiter=',', dtype=int)

        # Create a canvases that can fit the above video source size
        self.canvas = Canvas(self.root, width=400, height=300)
        self.info_canvas = Canvas(self.root, width=15, height=300)

        # Create side info window
        self.tracking_text = StringVar()
        self.text_box = Label(self.info_canvas, bg="green", textvariable=self.tracking_text, width=15, height=5)

        # Create readout window
        self.read_out = Text(self.info_canvas, bg="white", width=15, height=13)
        self.read_out.config(state='disabled')

        # Save navigation
        self.menubar = Menu(self.root)
        self.filemenu = Menu(self.menubar, tearoff=0)
        self.filemenu.add_command(label="Saves", command=self.saves_launch)

        self.filemenu.add_separator()

        self.filemenu.add_command(label="Exit", command=self.root.quit)
        self.menubar.add_cascade(label="File", menu=self.filemenu)

        # Place widgets
        self.canvas.pack(padx=5, pady=5, side=tkinter.LEFT)
        self.text_box.grid(row=0, column=1, pady=5)
        self.read_out.grid(row=1, column=1, pady=5)
        self.info_canvas.pack(padx=5, pady=5, side=tkinter.LEFT)


        # Update will be called after every delay
        self.delay = 15
        self.update()

        self.root.config(menu=self.menubar)
        self.root.mainloop()

    def update(self):
        intercept = None
        if self.cv.isDetected():
            if len(self.cv.pts) > 5 and self.cv.pts[0] is not None and self.cv.pts[1] is not None:
                intercept = self.cv.predict(self.aim.get_delay())

        # Get a frame from the video source
        ret, frame = self.vid.get_frame()

        # clean the frame to see just the target size of frame is 400x300pts
        frame, mask = self.cv.CleanUp(frame, self.colorLower, self.colorUpper)

        # Find the ball
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

        if self.cv.targetData[0] is not None:
            # draw a circle around the target
            cv2.circle(frame, (self.cv.targetData[0], self.cv.targetData[1]), self.cv.targetData[2], [255, 0, 0], 2)

        if len(self.cv.pred_pts) > 0 and self.cv.targetData[2] is not None:
            for i in range(len(self.cv.pred_pts)):
                if self.cv.pred_pts[i] is None:
                    continue
                # draw prediction circle
                if intercept is not None and intercept[0] == self.cv.pred_pts[i][0] and intercept[1] == self.cv.pred_pts[i][1]:
                    color = [0, 255, 0]
                else:
                    color = [114, 42, 203]
                cv2.circle(frame, (self.cv.pred_pts[i][0], self.cv.pred_pts[i][1]), (int(self.cv.targetData[2] / 2)), color, 2)

        if ret:
            self.photo = PIL.ImageTk.PhotoImage(image=PIL.Image.fromarray(frame))
        self.canvas.create_image(0, 0, image=self.photo, anchor=NW)

        message = 'None Detected'
        if self.cv.isDetected():
            message = 'Detected:    1\n'
            message = message + 'Size:       ' + str(int(self.cv.targetData[2])) + '\n'
            if self.cv.speed is not None:
                message = message + 'Speed:    ' + str(round(self.cv.speed, 4)) + 'm/s'
                # collect information
                saveframe_info = np.array([1, int(self.cv.targetData[2]), round(self.cv.speed, 4)])
            else:
                saveframe_info = np.array([1, int(self.cv.targetData[2]), 0])

            # collect video frame
            self.save_vid.appendleft(frame)

            self.save_info.appendleft(saveframe_info)
        elif len(self.save_vid) > 32 and self.save_vid[0] is not None:
            if not os.path.isdir('data/saves'):
                os.mkdir('data/saves')
            savefolder_name = 'data/saves/' + str(datetime.datetime.now()).replace(' ', '_')[0:-7].replace(':', '.')
            os.mkdir(savefolder_name)
            save_name = savefolder_name + '/info.csv' # 'data/saves/2021-11-02_15.45.43/info.csv'
            np.savetxt(save_name, np.array(self.save_info), delimiter=',')
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


        self.tracking_text.set(message)

        self.root.after(self.delay, self.update)

    def __del__(self):
        if self.save_thread is not None:
            self.save_thread.join()

    def saves_launch(self):
        self.save_thread = threading.Thread(target=SavesForm.SavesForm)
        try:
            self.save_thread.start()
        except:
            print("Error: Unable to start thread")
