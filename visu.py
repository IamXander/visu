import pyaudio
import time
import numpy as np
import tkinter as tk
from copy import copy, deepcopy

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

LED_FULL_BRIGHT = 255
LED_V_BRIGHT = 200
LED_BRIGHT = 150
LED_MEDIUM = 100
LED_DIM = 50
LED_V_DIM = 25
LED_VV_DIM = 10
LED_OFF = 0

SWITCH_TIME = 200
SHOW_DURATION = 500

import bibliopixel
from bibliopixel.drivers.serial import *
from bibliopixel.layout import *
# driver = Serial(num = (60*4), ledtype = LEDTYPE.WS2812B)
# led = Strip(driver)

import time
import random

class Application(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.pack()
        self.create_widgets()
        self.numLeds = 60*4
        driver = Serial(num = self.numLeds, ledtype = LEDTYPE.WS2812B)
        self.led = Strip(driver)
        self.plan = 1
        self.fadeToNextPlan = 0
        self.ledsPerBucket = int(self.numLeds/(len(BUCKET_SPLITS) - 1))
        self.allpoints = [[0,0,0] for i in range(self.numLeds)]
        self.reset()

    def create_widgets(self):
        self.cvs = tk.Canvas(self)
        self.cvs.config(height=700, width = 1000)
        self.cvs.pack(side="top")
        #self.cvs.grid(column=0, row=0, columnspan=3, rowspan=3, sticky=tk.N+tk.E+tk.W+tk.S)#pack(side="top")
        self.bars = [self.cvs.create_rectangle(0,100*i,100,100*(i+1), fill='#000') for i in range(len(BUCKET_SPLITS_LOCS)-1)]

        self.quit = tk.Button(self, text="QUIT", fg="red", command=root.destroy)
        self.quit.pack(side="bottom")

    def drawMonoBars(self, bars):
        for i in range(len(self.bars)):
            self.cvs.coords(self.bars[i], 0, 100*i, bars[i], 100*(i+1))

    def drawDualBars(self, left, right):
        #print(left)
        self.visu(left)
        for i in range(len(self.bars)):
            self.cvs.coords(self.bars[i], 500-left[i], 100*i, 500+right[i], 100*(i+1))

    def generateBrightColor(self):
        color = [0, 0, 0]
        while color == [0, 0, 0]:
            color = [random.randint(0, 1)*LED_FULL_BRIGHT, random.randint(0, 1)*LED_FULL_BRIGHT, random.randint(0, 1)*LED_FULL_BRIGHT]
        return color

    def reset(self):
        self.points = []
        self.fadeToNextCounter = 0
        self.fadeToNext = False
        self.color = self.generateBrightColor()
        self.ready = True
        self.locs = [[i*10, self.generateBrightColor()] for i in range(int(self.numLeds/10))]
        self.delta = 1
        self.maxBrightness = LED_FULL_BRIGHT
        self.fadeIntoNext = False

    def draw(self):
        self.led.all_off()
        for i in range(self.numLeds):
            self.led.set(i, (int(self.allpoints[i][0]), int(self.allpoints[i][1]), int(self.allpoints[i][2])))
        self.led.update()

    def all_off(self):
        self.led.all_off()
        for i in range(self.numLeds):
            self.allpoints[i] = [0, 0, 0]

    def setpointcolor(self, i, color):
        if i >= 0 and i < len(self.allpoints):
            self.allpoints[i] = color

    def visu(self, bars):
        # if sum(bars) < 1:
        #     self.fadeToNextCounter += 1
        # elif self.fadeToNextCounter <= SWITCH_TIME and self.fadeToNext == False:
        #     self.fadeToNextCounter = 0
        self.fadeToNextCounter += 1
        if self.fadeToNextCounter >= SHOW_DURATION:
            self.fadeToNext = True
        if self.plan == 0:
            if self.doShit(bars) == False:
                self.plan = 1
                self.reset()
        elif self.plan == 1:
            if self.eyes(bars) == False:
                self.plan = 2
                self.reset()
        elif self.plan == 2:
            if self.movement(bars) == False:
                self.plan = 3
                self.reset()
        elif self.plan == 3:
            if self.megaBar(bars) == False:
                self.plan = 4
                self.reset()
        elif self.plan == 4:
            if self.activeStars(bars) == False:
                self.plan = 5
                self.reset()
        elif self.plan == 5:
            if self.randomStars(bars) == False:
                self.plan = 0
                self.reset()
        # elif self.plan == 6:
        #     if self.chillStars() == False:
        #         self.plan = 0
        #         self.reset()
        if self.fadeToNext == True:
            if self.fadeOut() == True:
                self.plan = (self.plan + 1) % 6
                self.reset()
                self.maxBrightness = 0
                self.fadeIntoNext = True
        elif self.fadeIntoNext == True:
            if self.fadeIn() == True:
                self.maxBrightness = LED_FULL_BRIGHT
                self.fadeIntoNext = False
        self.draw()

    def fadeOut(self):
        self.maxBrightness -= 1.2
        for i in range(len(self.allpoints)):
            for j in range(len(self.allpoints[i])):
                if self.allpoints[i][j] > self.maxBrightness:
                    self.allpoints[i][j] = self.maxBrightness
        return self.maxBrightness <= 0

    def fadeIn(self):
        self.maxBrightness += 1.8
        for i in range(len(self.allpoints)):
            for j in range(len(self.allpoints[i])):
                if self.allpoints[i][j] > self.maxBrightness:
                    self.allpoints[i][j] = self.maxBrightness
        return self.maxBrightness >= LED_FULL_BRIGHT

    def drawStars(self, points):
        delStars = 0
        for i in range(len(points)-1, -1, -1):
            for j in [0, 1, 2]:
                if points[i][0][j] > 0:
                    points[i][0][j] -= points[i][1]
            self.setpointcolor(points[i][2],  points[i][0])
            if points[i][0][0] <= 0 and points[i][0][1] <= 0 and points[i][0][2] <= 0:
                del points[i]
                delStars += 1
                continue
        return delStars

    def activeStars(self, bars):
        if bars[0] > 40:
            self.points.append([[0, LED_FULL_BRIGHT, 0], random.uniform(8, 32), random.randint(0, self.numLeds)])
        if bars[1] > 30:
            self.points.append([[LED_FULL_BRIGHT, 0, 0], random.uniform(8, 32), random.randint(0, self.numLeds)])
        if bars[2] > 30:
            self.points.append([[0, 0, LED_FULL_BRIGHT], random.uniform(8, 32), random.randint(0, self.numLeds)])
        if bars[3] > 25:
            self.points.append([[LED_FULL_BRIGHT, LED_FULL_BRIGHT, 0], random.uniform(8, 32), random.randint(0, self.numLeds)])
        self.drawStars(self.points)

    def randomStars(self, bars):
        if bars[1] > 30:
            self.points.append([deepcopy(self.color), random.uniform(8, 32), random.randint(0, self.numLeds)])
        if bars[1] > 50:
            self.color = self.generateBrightColor()
            self.points.append([deepcopy(self.color), random.uniform(8, 32), random.randint(0, self.numLeds)])
            self.points.append([deepcopy(self.color), random.uniform(8, 32), random.randint(0, self.numLeds)])
            self.points.append([deepcopy(self.color), random.uniform(8, 32), random.randint(0, self.numLeds)])
        self.drawStars(self.points)

    def chillStars(self):
        while len(self.points) < 15:
            self.points.append([[1, 1, 1], -random.uniform(.4, 1), random.randint(0, self.numLeds)])
        for i in range(len(self.points)-1, -1, -1):
            if self.points[i][0][0] >= LED_MEDIUM or self.points[i][0][1] >= LED_MEDIUM or self.points[i][0][2] >= LED_MEDIUM:
                self.points[i][1] = -self.points[i][1]
        self.drawStars(self.points)

    def doShit(self, bars):
        for i in range(60*4):
            self.setpointcolor(i, [bars[1]*10, bars[2]/2, bars[3]*2])

    def eyes(self, bars):
        self.all_off()
        if bars[1] > 50:
            self.color = self.generateBrightColor()
        for i in range(len(bars)):
            for j in range(bars[i]+1):
                self.setpointcolor(i*self.ledsPerBucket + j, deepcopy(self.color))

    def movement(self, bars):
        self.all_off()
        if self.delta <= 0:
            self.delta = -.5 - (bars[3]/20)
        else:
            self.delta = .5 + (bars[3]/20)
        if bars[1] > 50:
            self.delta = -self.delta
        if bars[0] > 50:
            for i in range(len(self.locs)):
                self.locs[i][1] = self.generateBrightColor()
        for i in range(len(self.locs)):
            self.locs[i][0] += self.delta
            self.locs[i][0] = self.locs[i][0] % self.numLeds
            if self.locs[i][0] < 0:
                self.locs[i][0] = self.numLeds - 1
            self.setpointcolor(int(self.locs[i][0]), deepcopy(self.locs[i][1]))

    def megaBar(self, bars):
        self.all_off()
        if bars[1] > 50:
            self.color = self.generateBrightColor()
        for i in range(int(self.numLeds / 2) - (int(bars[0])), int(self.numLeds / 2) + (int(bars[0]))):
            self.setpointcolor(i, deepcopy(self.color))

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
app.master.minsize(100, 100)

p = pyaudio.PyAudio()

def callback(in_data, frame_count, time_info, status):
    #print(frame_count)
    #print(in_data)
    data = np.fromstring(in_data, dtype=np.int16)/WAVE_ABS_MAX #Normalize data
    dataEven = (data[::2])
    dataOdd = (data[1::2])
    specEven = abs(np.fft.rfft(dataEven))
    specOdd = abs(np.fft.rfft(dataOdd))

    barsEven = np.asarray([int(np.max(specEven[BUCKET_SPLITS_LOCS[i]:BUCKET_SPLITS_LOCS[i+1]])) for i in range(len(BUCKET_SPLITS_LOCS)-1)])
    barsOdd = np.asarray([int(np.max(specOdd[BUCKET_SPLITS_LOCS[i]:BUCKET_SPLITS_LOCS[i+1]])) for i in range(len(BUCKET_SPLITS_LOCS)-1)])
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
