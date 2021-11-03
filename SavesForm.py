import os
import tkinter
from tkinter import *
import PIL.Image, PIL.ImageTk
import cv2
import imutils


class SavesForm:
    def __init__(self):
        savesfolder = 'data/saves'

        self.root = Tk()
        self.root.title('Target Practice')
        self.root.iconbitmap('Art/Tpp-logo-horizontal.bmp')

        # Create canvases
        self.savelist_canvas = Canvas(self.root)

        # find total number of saves
        for base, dirs, files in os.walk(savesfolder):
            for directories in dirs:
                cursave_canvas = Canvas(self.savelist_canvas)
                datetitle_str = 'Date:'
                date_str = directories[0:10]
                timetitle_str = 'Time:'
                time_str = directories[12:].replace('.', ':')
                file_path = savesfolder + '/' + directories
                total_size = 0
                for dirpath, dirnames, filenames in os.walk(file_path):
                    for f in filenames:
                        fp = os.path.join(dirpath, f)
                        if not os.path.islink(fp):
                            total_size += os.path.getsize(fp)

                sizetitle_str = 'Size:'
                size_str = str(total_size / 1000) + 'MB'

                message = datetitle_str.ljust(25) + date_str.ljust(10) + '\n' + timetitle_str.ljust(24) + time_str.ljust(15) + '\n' + sizetitle_str.ljust(25) + size_str.ljust(10)

                # Create file details
                save_infobox = Label(cursave_canvas, bg="blue", text=message, height=8)

                cap = cv2.VideoCapture((file_path + '/video.avi'))

                ret, frame = cap.read()

                if ret:
                    thumbnail = imutils.resize(frame, width=15, height=8)
                    photo = PIL.ImageTk.PhotoImage(image=PIL.Image.fromarray(thumbnail))

                # Create Video Thumbnail
                save_thumbnail = Label(cursave_canvas, width=15, height=8)

                # Place save
                save_thumbnail.pack(padx=5, pady=2, side=tkinter.LEFT)
                save_infobox.pack(padx=5, pady=2, side=tkinter.LEFT)
                cursave_canvas.pack()
                cap.release()

        # Place the canvas
        self.savelist_canvas.pack(padx=5, pady=5)

        self.root.mainloop()
