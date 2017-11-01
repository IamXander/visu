import pyaudio
import time
import numpy as np
import tkinter as tk
from copy import copy, deepcopy
from collections import deque
import time
import random
import math
import bibliopixel
from bibliopixel.drivers.serial import *
from bibliopixel.layout import *
from visu_util import *
from fakeLed import *

from serial.serialutil import SerialException

VOLUME = 2

class VisuFunctions():
	def __init__(self):
		# try:
		# driverA = Serial(ledtype = LEDTYPE.WS2812B, num = 60*5, dev='COM3', device_id = 0)
		driverC = Serial(LEDTYPE.WS2812B, 60*5, dev='COM3', device_id = 2)
		driverB = ''
		print('here')
		while driverB == '':
			try:
				driverB = Serial(LEDTYPE.WS2812B, 60*5, dev='COM4', device_id = 1)
			except SerialException:
				print('Good try')
		self.led = Strip([driverB, driverC]) #[driverA, driverB, driverC])
			# driver = Serial(num = leds.numLeds, ledtype = LEDTYPE.WS2812B)
			# self.led = Strip(driver)
		# except ValueError:
			# print("NO LEDS FOUND")
			# self.led = FakeLed()
		self.plan = 1
		self.silentPlan = 1
		self.fadeToNextPlan = 0
		# self.ledsPerBucket = int(leds.numLeds/(len(BUCKET_SPLITS) - 1))
		self.allpoints = [[0,0,0] for i in range(leds.numLeds)]
		self.dq = deque([0], maxlen=int(fft.RATE / fft.FRAMES))
		self.functionList = [self.waves, self.activeStars, self.miniBars, self.randomStars, self.megaBar, self.rainbowStars, self.movement]
		self.silentList = [self.chillStars, self.pulsatingRainbow, self.pong]
		self.beatPause = 0
		self.frozen = False
		self.reset()

	def reset(self):
		self.points = []
		self.fadeToNextCounter = 0
		self.fadeToNext = False
		self.color = generateBrightColor()
		self.ready = True
		density = random.choice([5, 10, 20])
		self.locs = [[i*density, generateBrightColor()] for i in range(int(leds.numLeds/density))]
		self.delta = 1
		self.maxBrightness = led_brightness.LED_FULL_BRIGHT
		self.fadeIntoNext = False
		self.sections = random.choice([1, 2, 3, 4, 6])
		self.delay = 0
		self.pongDot = 0

	def getBeatAndPower(self, leftAudio, rightAudio):
		isBeat = False
		self.beatPause -= 1
		enew = np.sum(np.square(leftAudio)) + np.sum(np.square(rightAudio))
		if enew > 1.5 * np.average(self.dq) and self.beatPause <= 0:
			isBeat = True
			self.dq.clear()
			self.beatPause = 3
		self.dq.append(enew)
		return isBeat, enew

	def __draw(self):
		self.led.all_off()
		for i in range(leds.numLeds):
			self.led.set(i, (int(self.allpoints[i][0]), int(self.allpoints[i][1]), int(self.allpoints[i][2])))
		self.led.update()

	def all_off(self):
		self.led.all_off()
		for i in range(leds.numLeds):
			self.allpoints[i] = [0, 0, 0]

	def __setpointcolor(self, i, color):
		if i >= 0 and i < len(self.allpoints):
			self.allpoints[i] = color

	def render(self, leftAudio, rightAudio, leftBars, rightBars):
		isBeat, power = self.getBeatAndPower(leftAudio, rightAudio)
		self.fadeToNextCounter += 1
		if self.fadeToNextCounter >= shows.SHOW_DURATION and self.frozen == False:
			self.fadeToNext = True

		self.functionList[self.plan](leftAudio, rightAudio, leftBars, rightBars, isBeat, power)
		# self.silentList[self.silentPlan]()

		if self.fadeToNext == True:
			if self.fadeOut() == True:
				self.plan = (self.plan + 1) % len(self.functionList)
				self.silentPlan = (self.silentPlan + 1) % len(self.silentList)
				self.reset()
				self.maxBrightness = 0
				self.fadeIntoNext = True
		elif self.fadeIntoNext == True:
			if self.fadeIn() == True:
				self.maxBrightness = led_brightness.LED_FULL_BRIGHT
				self.fadeIntoNext = False
		self.__draw()

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
		return self.maxBrightness >= led_brightness.LED_FULL_BRIGHT

	def __drawStars(self, points):
		delStars = 0
		for i in range(len(points)-1, -1, -1):
			for j in [0, 1, 2]:
				if points[i][0][j] > 0:
					points[i][0][j] -= points[i][1]
			self.__setpointcolor(points[i][2],  points[i][0])
			if points[i][0][0] <= 0 and points[i][0][1] <= 0 and points[i][0][2] <= 0:
				del points[i]
				delStars += 1
				continue
		return delStars

	def activeStars(self, leftAudio, rightAudio, leftBars, rightBars, isBeat, power):
		if power >= power_cutoffs.HIGH:
			self.points.append([deepcopy(colors.RED), random.uniform(8, 32), random.randint(0, leds.numLeds-1)])
		if power >= power_cutoffs.MEDIUM:
			self.points.append([deepcopy(colors.GREEN), random.uniform(8, 32), random.randint(0, leds.numLeds-1)])
		if power >= power_cutoffs.LOW:
			self.points.append([deepcopy(colors.BLUE), random.uniform(8, 32), random.randint(0, leds.numLeds-1)])
		self.__drawStars(self.points)

	def randomStars(self, leftAudio, rightAudio, leftBars, rightBars, isBeat, power):
		if power >= power_cutoffs.LOW:
			self.points.append([deepcopy(self.color), random.uniform(8, 32), random.randint(0, leds.numLeds-1)])
		if power > power_cutoffs.MEDIUM:
			self.points.append([deepcopy(self.color), random.uniform(8, 32), random.randint(0, leds.numLeds-1)])
		if power > power_cutoffs.HIGH:
			self.color = generateBrightColor(self.color)
			self.points.append([deepcopy(self.color), random.uniform(8, 32), random.randint(0, leds.numLeds-1)])
			self.points.append([deepcopy(self.color), random.uniform(8, 32), random.randint(0, leds.numLeds-1)])
			self.points.append([deepcopy(self.color), random.uniform(8, 32), random.randint(0, leds.numLeds-1)])
		self.__drawStars(self.points)

	def rainbowStars(self, leftAudio, rightAudio, leftBars, rightBars, isBeat, power):
		if isBeat:
			speed = random.uniform(2, 4)
			pos = random.randint(0, leds.numLeds)
			for i in range(int(power/6)):
				self.points.append([deepcopy(gradients.RAINBOW[(pos + i) % leds.numLeds]), speed, (pos + i) % leds.numLeds])
		self.__drawStars(self.points)

	def waves(self, leftAudio, rightAudio, leftBars, rightBars, isBeat, power):
		self.all_off()
		self.delay -= 1;
		if isBeat and self.delay < 0: #There should be at least one space
			#location, color, quantity, speed, gradient
			self.delay = math.ceil(power/8)
			self.points.append([0, generateBrightColor(), self.delay, 1, random.randint(0, len(gradient_list.ALL)-1)])
		i = 0
		while i < len(self.points):
			for j in range(self.points[i][2]):
				grad = getattr(gradients, gradient_list.ALL[self.points[i][4]]);
				self.__setpointcolor(self.points[i][0]-j, deepcopy(grad[(self.points[i][0]-j) % len(grad)]))

			self.points[i][0]+=self.points[i][3]
			if self.points[i][0]-self.points[i][2] >= leds.numLeds:
				del self.points[i]
				i -= 1
			i+=1

	def miniBars(self, leftAudio, rightAudio, leftBars, rightBars, isBeat, power):
		self.delta+=.5
		self.all_off()
		if isBeat:
			self.color = generateBrightColor(self.color)
		for i in range(3):
			for j in range(min(leftBars[i]+1, int(leds.numLeds/6))):
				self.__setpointcolor(i*int(leds.numLeds/6) + j, deepcopy(gradients.RAINBOW[int(i*leds.numLeds/6 + j + self.delta) % len(gradients.RAINBOW)]))
			for j in range(min(rightBars[i]+1, int(leds.numLeds/6))):
			   	self.__setpointcolor(leds.numLeds - (i*int(leds.numLeds/6)) - j - 1, deepcopy(gradients.RAINBOW[int(leds.numLeds - (i*leds.numLeds/6) - j - 1+ self.delta) % len(gradients.RAINBOW)]))

	def movement(self, leftAudio, rightAudio, leftBars, rightBars, isBeat, power):
		self.all_off()
		if self.delta <= 0:
			self.delta = -.5 - (leftBars[3]/20)
		else:
			self.delta = .5 + (leftBars[3]/20)
		if isBeat:
			self.delta = -self.delta
			for i in range(len(self.locs)):
				self.locs[i][1] = generateBrightColor()
		for j in range(self.sections):
			for i in range(int(len(self.locs)*(j/self.sections)), int(len(self.locs)*((j+1)/self.sections))):
				self.locs[i][0] += self.delta * ((j%2)-.5) * 2
				self.locs[i][0] = ((self.locs[i][0]-int(leds.numLeds*(j/self.sections))) % int(leds.numLeds/self.sections)) + (int(leds.numLeds*(j/self.sections)))
				self.__setpointcolor(int(self.locs[i][0]), deepcopy(self.locs[i][1]))

	def megaBar(self, leftAudio, rightAudio, leftBars, rightBars, isBeat, power):
		self.all_off()
		if isBeat:
			self.color = generateBrightColor(self.color)
		for i in range(int(leds.numLeds / 2) - (int(max(leftBars[0], leftBars[1]))), int(leds.numLeds / 2) + (int(max(rightBars[0], rightBars[1])))):
			self.__setpointcolor(i, deepcopy(self.color))

	def pong(self):
		self.__setpointcolor(int(self.pongDot), [0, 0, 0])
		self.pongDot += self.delta
		if self.pongDot >= leds.numLeds-1 or self.pongDot <= 0:
			self.delta = -self.delta
			self.color = generateBrightColor(self.color)
		self.__setpointcolor(int(self.pongDot), deepcopy(self.color))

	def chillStars(self):
		while len(self.points) < 15:
			self.points.append([[1, 1, 1], -random.uniform(.4, 1), random.randint(0, leds.numLeds)])
		for i in range(len(self.points)-1, -1, -1):
			if self.points[i][0][0] >= led_brightness.LED_MEDIUM or self.points[i][0][1] >= led_brightness.LED_MEDIUM or self.points[i][0][2] >= led_brightness.LED_MEDIUM:
				self.points[i][1] = -self.points[i][1]
		self.__drawStars(self.points)

	def pulsatingRainbow(self):
		self.delta+=1
		for i in range(leds.numLeds):
			self.__setpointcolor(i, deepcopy(gradients.RGB[int((i + self.delta) % len(gradients.RGB))]))

class Application(tk.Frame):
	def __init__(self, master=None):
		super().__init__(master)
		self.pack()
		self.create_widgets()

	def create_widgets(self):
		self.cvs = tk.Canvas(self)
		self.cvs.config(height=700, width = 1000)
		self.cvs.pack(side="top")
		#self.cvs.grid(column=0, row=0, columnspan=3, rowspan=3, sticky=tk.N+tk.E+tk.W+tk.S)#pack(side="top")
		self.bars = [self.cvs.create_rectangle(0,100*i,100,100*(i+1), fill='#000') for i in range(len(fft.BUCKET_SPLITS_LOCS)-1)]

		self.quit = tk.Button(self, text="QUIT", fg="red", command=root.destroy)
		self.quit.pack(side="left")
		self.frozen = tk.Checkbutton(self, text="Freeze", onvalue=True, offvalue=False, variable=visu.frozen)
		self.frozen.pack(side="right")
		i = 0
		for f in visu.functionList:
			tmp = tk.Button(self, text=f.__name__, command=lambda:self.funcClicked(0))
			tmp.pack(side="right")
			i += 1

	def drawDualBars(self, leftBars, rightBars):
		for i in range(len(self.bars)):
			self.cvs.coords(self.bars[i], 500-leftBars[i], 100*i, 500+rightBars[i], 100*(i+1))

	def funcClicked(self, i):
		visu.plan = i
		print(visu.frozen)
		visu.frozen = True
		visu.reset()
		visu.all_off()

visu = VisuFunctions()

root = tk.Tk()
root.columnconfigure(0, weight=1)
root.rowconfigure(0, weight=1)

app = Application(master=root)
app.master.title("Visu")
app.master.minsize(100, 100)

p = pyaudio.PyAudio()

def callback(in_data, frame_count, time_info, status):
	data = np.fromstring(in_data, dtype=np.int16)/fft.WAVE_ABS_MAX #Normalize data
	dataEven = (data[::2]) #Right
	dataOdd = (data[1::2]) #Left
	specEven = abs(np.fft.rfft(dataEven))
	specOdd = abs(np.fft.rfft(dataOdd))

	barsEven = np.asarray([int(np.max(specEven[fft.BUCKET_SPLITS_LOCS[i]:fft.BUCKET_SPLITS_LOCS[i+1]])) for i in range(len(fft.BUCKET_SPLITS_LOCS)-1)])
	barsOdd = np.asarray([int(np.max(specOdd[fft.BUCKET_SPLITS_LOCS[i]:fft.BUCKET_SPLITS_LOCS[i+1]])) for i in range(len(fft.BUCKET_SPLITS_LOCS)-1)])
	app.drawDualBars(barsEven, barsOdd)
	visu.render(dataEven, dataOdd, barsEven, barsOdd)
	#return (in_data, pyaudio.paComplete)
	return (in_data, pyaudio.paContinue)

stream = p.open(format=p.get_format_from_width(fft.WIDTH), frames_per_buffer=fft.FRAMES, channels=fft.CHANNELS,
	rate=fft.RATE, input=True, output=False, stream_callback=callback)

stream.start_stream()

app.mainloop()

stream.stop_stream()
stream.close()

p.terminate()
