import datetime
import os
import tkinter as tk
import tkinter.ttk as ttk
import PIL.Image, PIL.ImageTk
import cv2
import imutils
import numpy as np

import Form
import pandas as pd


class Load:
    def __init__(self, _save_path):
        self.isAlive = False
        self.save_path = _save_path
        self.cur_frame = 0

        # Get video
        self.vid = Form.MyVideoCapture(self.save_path + '/video.avi')

        # Create window
        self.root = tk.Toplevel()
        self.root.title('Target Practice')
        self.root.iconbitmap('Art/Tpp-logo-horizontal.bmp')
        self.background = self.root.cget('background')

        # Create canvas
        self.vid_canvas = tk.Canvas(self.root)
        self.info_canvas = tk.Canvas(self.root, width=15, height=300)
        self.btn_canvas = tk.Canvas(self.root)

        # Create side info window
        self.tracking_text = tk.StringVar()
        self.text_box = tk.Label(self.info_canvas, bg="green", textvariable=self.tracking_text, width=15, height=5)

        # Create readout window
        self.read_out = tk.Text(self.info_canvas, bg="white", width=15, height=13)
        self.read_out.config(state='disabled')

        self.num_frames, self.length, self.info_rows = self.get_length()

        # Create video navigation slider
        self.navi_bar = ttk.Scale(self.root, from_=0, to=self.num_frames, orient=tk.HORIZONTAL, length=self.root.winfo_width(), command=self.slide)

        # Create pause/play button
        self.pbutton = tk.Button(self.btn_canvas, text='Play', command=self.play_pause)
        self.forward_btn = tk.Button(self.btn_canvas, text='Forward', command=self.forward)
        self.backward_btn = tk.Button(self.btn_canvas, text='backward', command=self.backward)

        # Place widgets
        self.vid_canvas.grid(padx=5, pady=5, row=0, column=0)
        self.text_box.grid(row=0, column=1, pady=5)
        self.read_out.grid(row=1, column=1, pady=5)
        self.info_canvas.grid(padx=5, pady=5, row=0, column=1)
        self.navi_bar.grid(padx=10, pady=5, row=1, column=0)
        self.pbutton.grid(padx=10, pady=10, row=0, column=1)
        self.forward_btn.grid(padx=10, pady=10, row=0, column=2)
        self.backward_btn.grid(padx=10, pady=10, row=0, column=0)
        self.btn_canvas.grid(row=2, column=0)


        # set delay and initialize updating
        self.delay = 15
        self.update()

        # start the main infinite loop for the window
        self.root.mainloop()

    def update(self):
        if self.cur_frame >= self.num_frames:
            self.cur_frame = self.num_frames
        # get the correct frame
        ret, frame = self.vid.get_frame(selected=self.cur_frame)
        if self.isAlive:
            self.cur_frame += 1

        if ret:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            self.photo = PIL.ImageTk.PhotoImage(image=PIL.Image.fromarray(frame))
        self.vid_canvas.create_image(0, 0, image=self.photo, anchor=tk.NW)

        frame_data = self.get_info()

        message = 'End of File'
        if frame_data is not None:
            message = 'Detected:    ' + str(frame_data[0]) + '\n'
            message = message + 'Size:       ' + str(frame_data[1]) + '\n'
            message = message + 'Speed:    ' + str(frame_data[2]) + 'm/s'

        self.tracking_text.set(message)

        self.navi_bar.config(value=self.cur_frame)

        self.root.after(self.delay, self.update)

    def get_length(self):
        # create video capture object
        data = cv2.VideoCapture(self.save_path + '/video.avi')

        # count the number of frames
        frames = data.get(cv2.CAP_PROP_FRAME_COUNT)
        fps = int(data.get(cv2.CAP_PROP_FPS))

        # calculate duration of the video
        seconds = int(frames / fps)
        video_time = str(datetime.timedelta(seconds=seconds))

        info_rows = pd.read_csv(self.save_path + '/info.csv').shape[0]

        return int(frames), video_time, info_rows

    def play_pause(self):
        cur_text = self.pbutton.cget('text')
        if cur_text == 'Play':
            btn_text = 'Pause'
        else:
            btn_text = 'Play'
        self.pbutton.config(text=btn_text)
        self.isAlive = not self.isAlive

    def forward(self):
        # Advance one frame
        if self.cur_frame < (self.num_frames - 1):
            self.cur_frame += 1

    def backward(self):
        # Reverse one frame
        if self.cur_frame > 0:
            self.cur_frame -= 1

    def slide(self, x):
        frame = int(self.navi_bar.get())
        if frame > 0 and frame < self.num_frames:
            self.cur_frame = frame

    def get_info(self):
        if self.cur_frame < self.info_rows:
            if self.cur_frame != 0:
                frame_data = pd.read_csv(self.save_path + '/info.csv', nrows=1, skiprows=(self.cur_frame - 1))
            else:
                frame_data = pd.read_csv(self.save_path + '/info.csv', nrows=1)

            frame_data = frame_data.to_numpy()

            if frame_data.shape != 3:
                frame_data = frame_data[0]
        else:
            frame_data = None

        return frame_data
