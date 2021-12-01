import os
import shutil
import tkinter as tk
import PIL.Image, PIL.ImageTk
import cv2
import imutils
import Form
import LoadForm


class SavesForm:
    def __init__(self):
        self.save_canvasfolder = 'data/saves'


        self.root = tk.Toplevel()
        self.root.title('Target Practice')
        self.root.iconbitmap('Art/Tpp-logo-horizontal.bmp')
        self.background = self.root.cget('background')

        # display for if there is no saves
        if not os.path.isdir(self.save_canvasfolder):
            self.no_saves = tk.Label(self.root, text='No Saves Found', padx=25, pady=25).pack()
            self.root.mainloop()
        else:
            # save arrays
            self.thumbnails = []
            self.save_canvas = []
            self.save_paths = []

            # delete button array
            self.deletes = []

            # current save length
            self.save_count = 0

            # Create canvas for saves to be placed on
            self.savelist_canvas = tk.Canvas(self.root)

            # create saves onto canvas
            self.save_list()

            # updating every delay
            self.delay = 15
            self.update()

            self.root.mainloop()

    def update(self):
        update_count = 0
        for base, dirs, files in os.walk(self.save_canvasfolder):
            for directories in dirs:
                update_count += 1
        if update_count > self.save_count:
            self.clear_list()
            self.save_list()

        self.root.after(self.delay, self.update)

    def save_list(self):
        # find all saves and add them to display canvas
        self.save_count = 0
        for base, dirs, files in os.walk(self.save_canvasfolder):
            for directories in dirs:
                self.save_count += 1
                cursave = self.save_count - 1

                cursave_canvas = tk.Canvas(self.savelist_canvas)

                datetitle_str = 'Date:'
                date_str = directories[0:10]
                timetitle_str = 'Time:'
                time_str = directories[12:].replace('.', ':')
                file_path = self.save_canvasfolder + '/' + directories
                total_size = 0
                for dirpath, dirnames, filenames in os.walk(file_path):
                    for f in filenames:
                        fp = os.path.join(dirpath, f)
                        if not os.path.islink(fp):
                            total_size += os.path.getsize(fp)

                sizetitle_str = 'Size:'
                size_str = str(total_size / 1000) + 'MB'

                message = datetitle_str.ljust(25) + date_str.ljust(100) + '\n' + timetitle_str.ljust(24) + \
                          time_str.ljust(105) + '\n' + sizetitle_str.ljust(25) + size_str.ljust(100)

                # Create file details
                save_infobox = tk.Label(cursave_canvas, bg=self.background, text=message, height=6)

                save_path = self.save_canvasfolder + '/' + directories
                cap = Form.MyVideoCapture(video_source=(save_path + '/video.avi'))

                ret, frame = cap.get_frame()

                if ret:
                    self.save_paths.append(save_path)
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    thumbnail = imutils.resize(frame, width=150, height=80)
                    photo = PIL.ImageTk.PhotoImage(image=PIL.Image.fromarray(thumbnail))

                # Create Video Thumbnail
                self.thumbnails.append(photo)
                save_thumbnail = tk.Label(cursave_canvas, image=self.thumbnails[len(self.thumbnails) - 1], width=150,
                                       height=80)

                # Create Delete Button
                def delete(event):
                    y = event.y_root - self.root.winfo_y()
                    selected_save = int((y - 40) / 100)
                    self.remove(selected_save)
                del_btn = tk.Button(cursave_canvas, text="Delete")


                #place save
                save_thumbnail.pack(padx=5, pady=2, side=tk.LEFT)
                save_infobox.pack(padx=5, pady=2, side=tk.LEFT)
                del_btn.pack(padx=5, pady=2, side=tk.RIGHT)

                del_btn.bind("<Button-1>", delete)
                self.deletes.append(del_btn)

                self.save_canvas.append(cursave_canvas)
                self.save_canvas[cursave].pack()

        def hover(event):
            self.root.config(bg=self.background)
            if not isinstance(event.widget, tk.Canvas) and event.widget is not self.root:
                event.widget.config(bg="green")

        def no_hover(event):
            if not isinstance(event.widget, tk.Canvas) and event.widget is not self.root:
                event.widget.config(bg=self.background)
            pass

        def click(event):
            x = event.x_root - self.root.winfo_x()
            if x < 600:
                y = event.y_root - self.root.winfo_y()
                selected_save = int((y - 40) / 100)
                self.load_save(selected_save)

        # Add events
        self.root.bind('<Enter>', hover)
        self.root.bind('<Leave>', no_hover)
        self.root.bind('<Button-1>', click)

        # Place the canvas
        self.savelist_canvas.pack(padx=5, pady=5)

    def clear_list(self):
        self.savelist_canvas.destroy()
        self.save_canvas.clear()
        self.savelist_canvas = tk.Canvas(self.root)
        self.thumbnails = []

    def load_save(self, save_num):
        save_file = self.save_paths[save_num]
        self.root.destroy()
        LoadForm.Load(save_file)

    def remove(self, save_num):
        save_file = self.save_paths[save_num]
        self.save_count -= 1
        self.clear_list()
        shutil.rmtree(save_file, onerror=self.errhandler)
        del self.save_paths[save_num]
        self.save_list()

    def errhandler(self, func, path, exc_info):
        print(exc_info)
