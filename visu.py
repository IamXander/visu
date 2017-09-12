import pyaudio
import time
import numpy as np
import tkinter as tk

WIDTH = 2
CHANNELS = 2
RATE = 44100
FRAMES = 2**10
WAVE_MIN = -32768
WAVE_MAX = 32767
WAVE_ABS_MAX = 32768
SPACES = 100
BUCKET_SIZE = 2**6
BUCKET_SPLITS = [20, 60, 250, 500, 2000, 4000, 6000, 20000]
FREQ = np.fft.rfftfreq(FRAMES, 1/RATE)
BUCKET_SPLITS_LOCS = [np.where(FREQ >= x)[0][0] for x in BUCKET_SPLITS]

class Application(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.pack()
        self.create_widgets()

    def create_widgets(self):
        self.cvs = tk.Canvas(self)
        self.cvs.config(height=1000, width = 1000)
        self.cvs.pack(side="top")
        #self.cvs.grid(column=0, row=0, columnspan=3, rowspan=3, sticky=tk.N+tk.E+tk.W+tk.S)#pack(side="top")
        self.bars = [self.cvs.create_rectangle(0,100*i,100,100*(i+1), fill='#000') for i in range(len(BUCKET_SPLITS_LOCS)-1)]

        self.quit = tk.Button(self, text="QUIT", fg="red", command=root.destroy)
        self.quit.pack(side="bottom")

    def drawMonoBars(self, bars):
        for i in range(len(self.bars)):
            self.cvs.coords(self.bars[i], 0, 100*i, bars[i], 100*(i+1))

    def drawDualBars(self, left, right):
        for i in range(len(self.bars)):
            self.cvs.coords(self.bars[i], 500-left[i], 100*i, 500+right[i], 100*(i+1))

    def printBars(self, bars):
        l = ''
        for b in bars:
            l += ' ' * b
            l += '#\n'
        l += '\n\n\n\n\n\n'
        print(l)

root = tk.Tk()
root.columnconfigure(0, weight=1)
root.rowconfigure(0, weight=1)

app = Application(master=root)
app.master.title("Visu")
app.master.minsize(1000, 1000)

p = pyaudio.PyAudio()

def callback(in_data, frame_count, time_info, status):
    #print(frame_count)
    #print(in_data)
    data = np.fromstring(in_data, dtype=np.int16)/WAVE_ABS_MAX #Normalize data
    dataEven = (data[::2])
    dataOdd = (data[1::2])
    specEven = abs(np.fft.rfft(dataEven))
    specOdd = abs(np.fft.rfft(dataOdd))

    barsEven = [int(np.max(specEven[BUCKET_SPLITS_LOCS[i]:BUCKET_SPLITS_LOCS[i+1]])) for i in range(len(BUCKET_SPLITS_LOCS)-1)]
    barsOdd = [int(np.max(specOdd[BUCKET_SPLITS_LOCS[i]:BUCKET_SPLITS_LOCS[i+1]])) for i in range(len(BUCKET_SPLITS_LOCS)-1)]
    app.drawDualBars(barsEven, barsOdd)
    #return (in_data, pyaudio.paComplete)
    return (in_data, pyaudio.paContinue)

stream = p.open(format=p.get_format_from_width(WIDTH),
                frames_per_buffer=FRAMES,
                channels=CHANNELS,
                rate=RATE,
                input=True,
                output=False,
                stream_callback=callback)

stream.start_stream()

app.mainloop()

stream.stop_stream()
stream.close()

p.terminate()
