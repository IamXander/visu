import pyaudio
import time
import numpy as np
import tkinter as tk
from copy import copy, deepcopy
from collections import deque

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
SHOW_DURATION = 700

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
        self.plan = 0
        self.fadeToNextPlan = 0
        # self.ledsPerBucket = int(self.numLeds/(len(BUCKET_SPLITS) - 1))
        self.allpoints = [[0,0,0] for i in range(self.numLeds)]
        self.dq = deque([0],maxlen=int(RATE / FRAMES))
        self.chunkedRainbow = [[0, 255, 0], [165, 255, 0], [255, 255, 0], [255, 0, 0], [0, 0, 255], [0, 75, 130], [0, 139, 255]]
        self.rainbow = [[0, 0, 0]] * self.numLeds
        rainbowIdx = 0
        for i in range(len(self.chunkedRainbow)-1):
            dist = int(self.numLeds / (len(self.chunkedRainbow)-1))
            delta = [(self.chunkedRainbow[i+1][j] - self.chunkedRainbow[i][j])/dist for j in range(3)]
            for q in range(dist):
                self.rainbow[rainbowIdx] = [self.chunkedRainbow[i][j] + (delta[j]*q) for j in range(3)]
                rainbowIdx += 1
        self.reset()

    def create_widgets(self):
        self.cvs = tk.Canvas(self)
        self.cvs.config(height=700, width = 1000)
        self.cvs.pack(side="top")
        #self.cvs.grid(column=0, row=0, columnspan=3, rowspan=3, sticky=tk.N+tk.E+tk.W+tk.S)#pack(side="top")
        self.bars = [self.cvs.create_rectangle(0,100*i,100,100*(i+1), fill='#000') for i in range(len(BUCKET_SPLITS_LOCS)-1)]

        self.quit = tk.Button(self, text="QUIT", fg="red", command=root.destroy)
        self.quit.pack(side="bottom")

    def drawDualBars(self, leftAudio, rightAudio, leftBars, rightBars):
        isBeat = False
        enew = np.sum(np.square(leftAudio)) + np.sum(np.square(rightAudio))
        if enew > 1.5 * np.average(self.dq):
            isBeat = True
            self.dq.clear()
        self.dq.append(enew)
        self.visu(leftAudio, rightAudio, leftBars, rightBars, isBeat)
        for i in range(len(self.bars)):
            self.cvs.coords(self.bars[i], 500-leftBars[i], 100*i, 500+rightBars[i], 100*(i+1))

    def generateBrightColor(self, otherColor=[0,0,0]):
        color = [0, 0, 0]
        while color == [0, 0, 0] or color == otherColor:
            color = [random.randint(0, 1)*LED_FULL_BRIGHT, random.randint(0, 1)*LED_FULL_BRIGHT, random.randint(0, 1)*LED_FULL_BRIGHT]
        return color

    def reset(self):
        self.points = []
        self.fadeToNextCounter = 0
        self.fadeToNext = False
        self.color = self.generateBrightColor()
        self.ready = True
        density = random.choice([5, 10, 20])
        self.locs = [[i*density, self.generateBrightColor()] for i in range(int(self.numLeds/density))]
        self.delta = 1
        self.maxBrightness = LED_FULL_BRIGHT
        self.fadeIntoNext = False
        self.sections = random.choice([1, 2, 3, 4, 6])

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

    def visu(self, leftAudio, rightAudio, leftBars, rightBars, isBeat):
        # if sum(bars) < 1:
        #     self.fadeToNextCounter += 1
        # elif self.fadeToNextCounter <= SWITCH_TIME and self.fadeToNext == False:
        #     self.fadeToNextCounter = 0
        self.fadeToNextCounter += 1
        if self.fadeToNextCounter >= SHOW_DURATION:
            self.fadeToNext = True
        # if self.plan == 0:
        #     if self.doShit(leftBars) == False:
        #         self.plan = 1
        #         self.reset()
        if self.plan == 0:
            if self.movement(leftBars, rightBars, isBeat) == False:
                self.plan = 1
                self.reset()
        elif self.plan == 1:
            if self.rainbowStars(isBeat) == False:
                self.plan = 2
                self.reset()
        elif self.plan == 2:
            if self.miniBars(leftBars, rightBars, isBeat) == False:
                self.plan = 3
                self.reset()
        elif self.plan == 3:
            if self.activeStars(leftBars) == False:
                self.plan = 4
                self.reset()
        elif self.plan == 4:
            if self.megaBar(leftBars, rightBars, isBeat) == False:
                self.plan = 5
                self.reset()
        elif self.plan == 5:
            if self.randomStars(leftBars) == False:
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

    def rainbowStars(self, isBeat):
        if isBeat:
            speed = random.uniform(2, 4)
            pos = random.randint(0, self.numLeds)
            for i in range(random.randint(5, 15)):
                self.points.append([deepcopy(self.rainbow[(pos + i) % self.numLeds]), speed, (pos + i) % self.numLeds])
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

    def miniBars(self, leftBars, rightBars, isBeat):
        self.all_off()
        if isBeat:
            self.color = self.generateBrightColor(self.color)
        for i in range(3):
            for j in range(min(leftBars[i]+1, int(self.numLeds/6))):
                self.setpointcolor(i*int(self.numLeds/6) + j, deepcopy(self.rainbow[i*int(self.numLeds/6) + j]))
            for j in range(min(rightBars[i]+1, int(self.numLeds/6))):
               self.setpointcolor(self.numLeds - (i*int(self.numLeds/6)) - j - 1, deepcopy(self.rainbow[self.numLeds - (i*int(self.numLeds/6)) - j - 1]))

    def movement(self, leftBars, rightBars, isBeat):
        self.all_off()
        if self.delta <= 0:
            self.delta = -.5 - (leftBars[3]/20)
        else:
            self.delta = .5 + (leftBars[3]/20)
        if isBeat:
            self.delta = -self.delta
            for i in range(len(self.locs)):
                self.locs[i][1] = self.generateBrightColor()
        for j in range(self.sections):
            for i in range(int(len(self.locs)*(j/self.sections)), int(len(self.locs)*((j+1)/self.sections))):
                self.locs[i][0] += self.delta * ((j%2)-.5) * 2
                self.locs[i][0] = ((self.locs[i][0]-int(self.numLeds*(j/self.sections))) % int(self.numLeds/self.sections)) + (int(self.numLeds*(j/self.sections)))
                self.setpointcolor(int(self.locs[i][0]), deepcopy(self.locs[i][1]))

    def megaBar(self, leftBars, rightBars, isBeat):
        self.all_off()
        if isBeat:
            self.color = self.generateBrightColor(self.color)
        for i in range(int(self.numLeds / 2) - (int(max(leftBars[0], leftBars[1]))), int(self.numLeds / 2) + (int(max(rightBars[0], rightBars[1])))):
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
    dataEven = (data[::2]) #Right
    dataOdd = (data[1::2]) #Left
    specEven = abs(np.fft.rfft(dataEven))
    specOdd = abs(np.fft.rfft(dataOdd))

    barsEven = np.asarray([int(np.max(specEven[BUCKET_SPLITS_LOCS[i]:BUCKET_SPLITS_LOCS[i+1]])) for i in range(len(BUCKET_SPLITS_LOCS)-1)])
    barsOdd = np.asarray([int(np.max(specOdd[BUCKET_SPLITS_LOCS[i]:BUCKET_SPLITS_LOCS[i+1]])) for i in range(len(BUCKET_SPLITS_LOCS)-1)])
    app.drawDualBars(dataEven, dataOdd, barsEven, barsOdd)
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
