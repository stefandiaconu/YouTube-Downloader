import tkinter as tk
from tkinter import ttk
from tkinter import Frame, filedialog, Menu, TclError, messagebox as mBox
import platform
from pytube import YouTube, exceptions
import threading
import queue
import os.path
import sys


class Main(Frame):
    def __init__(self, window, *args, **kwargs):
        Frame.__init__(self, window, *args, **kwargs)
        self.window = window
        self.window.title("YouTube Downloader")
        self.window.rowconfigure(0, weigh=1)
        self.window.columnconfigure(0, weight=1)
        self.format_tuple = ()
        self.step = 0
        self.bytes = 0
        self.max_bytes = 0

        # Create a Queue
        self.guiQueue = queue.Queue()

        self.create_widgets()

        self.path = os.path.abspath(os.getcwd())

    def create_widgets(self):
        # Variables
        self.url_var = tk.StringVar()
        # self.url_var.trace_add('write', self.populate_format)
        self.save_to_var = tk.StringVar()
        self.format_var = tk.StringVar()
        self.format_var.trace_add('write', self.check_audio)
        self.includes_var = tk.StringVar()
        self.percent_var = tk.StringVar()
        self.bar_var = tk.IntVar()
        self.convert_var = tk.StringVar()

        # Create popup menu for Copy/Paste
        self.m = Menu(self.window, tearoff=0)
        self.m.add_command(label="Cut")
        self.m.add_command(label="Copy")
        self.m.add_command(label="Paste")

        # Main frame
        self.main_frame = tk.Frame(self.window)
        self.main_frame.grid(column=0, row=0, sticky='wne', padx=10, pady=10)
        self.main_frame.rowconfigure(2, weight=1)
        self.main_frame.columnconfigure(0, weight=1)
        self.main_frame.columnconfigure(1, weight=1)

        self.url_frame = ttk.Frame(self.main_frame)
        self.url_frame.grid(column=0, row=0, columnspan=2, sticky='enw')
        self.url_frame.columnconfigure(1, weight=1)
        self.url_label = ttk.Label(self.url_frame, text="URL")
        self.url_label.grid(column=0, row=0, sticky='w')
        self.url_entry = ttk.Entry(self.url_frame, textvariable=self.url_var)
        self.url_entry.grid(column=1, row=0, sticky='ew')
        self.save_to_button = ttk.Button(self.url_frame, text="Save To", command=self.save_to)
        self.save_to_button.grid(column=0, row=1, sticky='w')
        self.save_to_entry = ttk.Entry(self.url_frame, textvariable=self.save_to_var)
        self.save_to_entry.grid(column=1, row=1, sticky='ew')

        self.download_frame = tk.Frame(self.main_frame)
        self.download_frame.columnconfigure(2, weight=1)
        self.download_frame.columnconfigure(3, weight=1)
        # self.download_frame.columnconfigure(1, weight=1)
        self.download_frame.grid(column=0, row=1, columnspan=2, pady=5, sticky='ew')
        self.load_url = ttk.Button(self.download_frame, text="Load URL", command=self.populate_format)
        self.load_url.grid(column=0, row=0, ipady=10)
        self.format_combo = ttk.Combobox(self.download_frame, textvariable=self.format_var)
        self.format_combo.grid(column=1, row=0, padx=10)
        self.includes_audio = ttk.Label(self.download_frame, textvariable=self.includes_var, width=20)
        self.includes_audio.grid(column=2, row=0, padx=10)
        self.download_button = ttk.Button(self.download_frame, text="Download Video", command=self.download_video)
        self.download_button.grid(column=3, row=0, ipadx=30, ipady=10, sticky='e')
        self.download_label = ttk.Label(self.download_frame, textvariable=self.percent_var)
        self.download_label.grid(column=0, row=1, sticky='ew', columnspan=4)
        self.download_bar = ttk.Progressbar(self.download_frame, orient=tk.HORIZONTAL, mode='determinate', variable=self.bar_var)
        self.download_bar.grid(column=0, row=2, columnspan=4, sticky='ew', pady=10)

        # create a Treeview
        self.tree = ttk.Treeview(self.main_frame, show='headings', columns=('Name', 'Format', 'Size', 'Resolution'))
        self.tree.grid(column=0, row=2, columnspan=2, sticky='wne')
        self.tree.bind('<<TreeviewSelect>>', self.file_to_convert)

        self.tree.column('Name', width=250, anchor='center')
        self.tree.heading('Name', text='Name')
        self.tree.column('Format', width=30, anchor='center')
        self.tree.heading('Format', text='Format')
        self.tree.column('Size', width=70, anchor='center')
        self.tree.heading('Size', text='Size')
        self.tree.column('Resolution', width=70, anchor='center')
        self.tree.heading('Resolution', text='Resolution')

        self.check_platform()

        self.convert_frame = ttk.Frame(self.main_frame)
        self.convert_frame.grid(column=0, row=3, columnspan=2, sticky='ew')
        # self.convert_frame.columnconfigure(0, weight=1)
        self.convert_frame.columnconfigure(2, weight=1)
        # self.convert_frame.columnconfigure(2, weight=1)
        # self.convert_frame.columnconfigure(2, weight=1)
        self.file_label = ttk.Label(self.convert_frame, text="File name")
        self.file_label.grid(column=0, row=0)
        self.convert_entry = ttk.Entry(self.convert_frame, textvariable=self.convert_var)
        self.convert_entry.grid(column=1, row=0, sticky='ew')
        self.convert_progress = ttk.Progressbar(self.convert_frame, orient=tk.HORIZONTAL, mode='indeterminate')
        self.convert_progress.grid(column=2, row=0, ipadx=10, sticky='ew')
        self.convert_button = ttk.Button(self.convert_frame, text="Convert Audio", command=self.convert_video)
        self.convert_button.grid(column=3, row=0, ipadx=30, ipady=10, sticky='e')

    def save_to(self):
        file_path = filedialog.askdirectory()
        self.save_to_var.set(file_path)
        self.path = self.save_to_var.get()

    def popup(self, event):
        try:
            self.m.entryconfig("Cut", command=lambda: event.widget.event_generate("<<Cut>>"))
            self.m.entryconfig("Copy", command=lambda: event.widget.event_generate("<<Copy>>"))
            self.m.entryconfig("Paste", command=lambda: event.widget.event_generate("<<Paste>>"))
            self.m.tk.call("tk_popup", self.m, event.x_root, event.y_root)
        finally:
            self.m.grab_release()

    def check_platform(self):
        plt = platform.system()
        if plt == "Windows":
            print("Your system is Windows")
            self.url_entry.bind("<Button-3>", self.popup)
            self.save_to_entry.bind("<Button-3>", self.popup)
        elif plt == "Linux":
            print("Your system is Linux")
            self.url_entry.bind("<Button-3>", self.popup)
            self.save_to_entry.bind("<Button-3>", self.popup)
        elif plt == "Darwin":
            print("Your system is MacOS")
            self.url_entry.bind("<Button-2>", self.popup)
            self.save_to_entry.bind("<Button-2>", self.popup)
        else:
            print("Unidentified system")
            mBox.showinfo("Copy/Paste functionality not working.")

    def file_to_convert(self, *args):
        # Reset the convert progressbar if used before
        self.convert_progress.stop()

        item = self.tree.focus()
        item = self.tree.item(item)
        self.video_file = item['text']
        title_file = item['values'][0]
        self.convert_var.set(title_file)

    def convert_video(self, *args):
        if len(self.convert_var.get()) > 0:
            try:
                from pydub import AudioSegment
                print("Alabama", self.video_file)
                if os.path.isfile(self.video_file):
                    self.convert_progress.start()
                    self.convert_progress.step(10)
                    self.convert_progress.update_idletasks()
                    audio = AudioSegment.from_file(self.video_file)
                    new_file = self.video_file.replace("mp4", "mp3")
                    audio.export(new_file, format="mp3", codec="libmp3lame")
                    # self.convert_progress.stop()
                    # mBox.showinfo("Convert to MP3", "The video has been converted from MP4 to MP3.")
                else:
                    mBox.showerror("Convert to MP3", "The file to convert doesn't exists!\nPlease check the folder for the actual file!")
            except:
                mBox.showerror("Convert to MP3", "The conversion to MP3 failed!")
        else:
            mBox.showwarning("Convert to MP3", "No file selected from the list to be converted!")

    def check_audio(self, *args):
        """ Check is current stream has audio"""
        if self.yt.streams[self.format_combo.current()].includes_audio_track:
            self.includes_var.set("Video includes audio? Yes")
        else:
            self.includes_var.set("Video includes audio? No")

    def download_video(self):
        if len(self.url_entry.get()) > 0:
            self.stream = self.yt.streams[self.format_combo.current()]

            # Set progress bar's maximum to video size
            self.max_bytes = self.stream.filesize
            self.download_bar['maximum'] = 100
            self.download_bar['value'] = self.step

            self.t1 = threading.Thread(target=self.fill_bar, args=[])
            self.t1.start()

        else:
            mBox.showwarning("URL Error", "You have not entered an Url.\nPlease enter a valid YouTuber Url to download a video.")

    def populate_format(self, *args):
        """ Get the streams from URL, filter only the mp4 streams, extract the resolution and fps.
            Populate the combo box with the extracted values. """
        # TODO extract everything in a different thread
        # Reset the convert progressbar if used before
        self.convert_progress.stop()

        self.format_combo['values'] = ()
        try:
            self.yt = YouTube(self.url_entry.get(), on_progress_callback=self.progress_bar, on_complete_callback=self.insert_tree)

            for stream in self.yt.streams.filter(subtype="mp4"):
                if stream.includes_video_track:
                    self.format_tuple += (str(stream.mime_type) + " " + str(stream.resolution) + " " + str(stream.fps) + "fps",)

        except exceptions.VideoUnavailable as videoUnavailable:
            mBox.showerror("Error", "Something wrong happened!\nError on line {}".format(sys.exc_info()[-1].tb_lineno) + ". " + str(videoUnavailable.__doc__))
        except exceptions.RegexMatchError as regexError:
            mBox.showerror("Error", "Something wrong happened!\nError on line {}".format(sys.exc_info()[-1].tb_lineno) + ". " + str(regexError.__doc__))
        except exceptions.HTMLParseError as htmlParseError:
            mBox.showerror("Error", "Something wrong happened!\nError on line {}".format(sys.exc_info()[-1].tb_lineno) + ". " + str(htmlParseError.__doc__))
        except exceptions.ExtractError as extractError:
            mBox.showerror("Error", "Something wrong happened!\nError on line {}".format(sys.exc_info()[-1].tb_lineno) + ". " + str(extractError.__doc__))
        except exceptions.PytubeError as pytubeError:
            mBox.showerror("Error", "Something wrong happened!\nError on line {}".format(sys.exc_info()[-1].tb_lineno) + ". " + str(pytubeError.__doc__))
        except KeyError as io:
            mBox.showerror("Error", "Something wrong happened!\nError on line {}".format(sys.exc_info()[-1].tb_lineno) + ". " + str(io.__doc__) + " " + str(io))
        except:
            mBox.showerror("Error", "Something wrong happened!")

        if len(self.format_tuple) > 0:
            self.format_combo['values'] = self.format_tuple
            self.format_combo.current(0)
            self.check_audio()

    def progress_bar(self, chunk, file_handle, bytes_remaining):
        remaining = (100 * bytes_remaining) / self.max_bytes
        self.step = 100 - int(remaining)
        self.guiQueue.put(self.step)
        self.window.after(1000, self.listen_result)

    def fill_bar(self):
        if len(self.save_to_var.get()) > 0:
            self.path = self.save_to_var.get()
        if os.path.isfile(self.path + "/" + str(self.format_combo.current()) + "_" + self.stream.default_filename):
            mBox.showerror("Download error", "This file already exists!\nPlease check again!")
        elif not os.path.isdir(self.path):
            mBox.showerror("Download error", "The selected path does not exists!\nPlease check again!")
        else:
            self.stream.download(output_path=self.path, filename_prefix=str(self.format_combo.current()) + "_")

    def listen_result(self):
        try:
            self.step = self.guiQueue.get_nowait()
            self.bar_var.set(self.step)
            self.percent_var.set("Downloading...  " + str(self.step) + "%")
            self.window.after(1000, self.listen_result)
        except queue.Empty:
            # self.window.after(100, self.listen_result)
            pass

    def insert_tree(self, *args):
        """ Insert details of downloaded video into the tree. """
        self.percent_var.set("Downloading...  " + str(self.step) + "% Completed!")
        iid = self.path + "/" + str(self.format_combo.current()) + "_" + self.stream.default_filename
        name = str(self.format_combo.current()) + "_" + self.stream.default_filename
        video_format = "mp4"
        size = str(round(self.stream.filesize * 0.000001, 1)) + "MB"
        resolution = self.set_resolution()
        try:
            self.tree.insert('', 'end', iid=iid, text=iid, values=(name, video_format, size, resolution))
        except TclError as err:
            mBox.showerror("Download error", "Error after download!\nError on line {}".format(sys.exc_info()[-1].tb_lineno) + ". " + str(err))

    def set_resolution(self):
        """ Label the resolution of the video """
        if self.stream.resolution == "2160p":
            return "3840x2160"
        elif self.stream.resolution == "1440p":
            return "2560x1440"
        elif self.stream.resolution == "1080p":
            return "1920x1080"
        elif self.stream.resolution == "720p":
            return "1280x720"
        elif self.stream.resolution == "480p":
            return "854x480"
        elif self.stream.resolution == "360p":
            return "640x360"
        elif self.stream.resolution == "240p":
            return "426x240"
        elif self.stream.resolution == "144p":
            return "256x144"
        else:
            return "No resolution detected"


# Start main loop
if __name__ == "__main__":
    root = tk.Tk()
    # set up widgets here, do your grid/pack/place
    # root.geometry() will return '1x1+0+0' here
    root.update()
    # now root.geometry() returns valid size/placement
    root.minsize(root.winfo_width(), root.winfo_height())
    main = Main(root)
    main.window.mainloop()
