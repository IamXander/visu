import random
import numpy as np

class led_brightness:
	LED_FULL_BRIGHT = 255
	LED_V_BRIGHT = 200
	LED_BRIGHT = 150
	LED_MEDIUM = 100
	LED_DIM = 50
	LED_V_DIM = 25
	LED_VV_DIM = 10
	LED_OFF = 0

class power_cutoffs:
	OFF = 0
	LOW = 15
	MEDIUM = 30
	HIGH = 45

class shows:
	SWITCH_TIME = 200
	SHOW_DURATION = 100000

class fft:
	FREQ = 6
	WIDTH = 2
	CHANNELS = 2
	RATE = 44100
	FRAMES = 2**10
	WAVE_MIN = -32768
	WAVE_MAX = 32767
	WAVE_ABS_MAX = 32768
	# BUCKET_SIZE = 2**6
	BUCKET_SPLITS = [20, 60, 250, 500, 2000, 4000, 6000, 20000]
	FREQ = np.fft.rfftfreq(FRAMES, 1/RATE)
	BUCKET_SPLITS_LOCS = []
	for x in BUCKET_SPLITS:
		i = 0
		for y in FREQ:
			if y > x:
				BUCKET_SPLITS_LOCS.append(i)
				break
			i += 1

class leds:
	numLeds = (60*4)+(60*5)

class colors:
	RED = [0, 255, 0]
	BLUE = [0, 0, 255]
	GREEN = [255, 0, 0]

def generateGradient(colors, positions):
	rainbowIdx = 0
	grad = [0] * positions[-1]
	for i in range(len(colors)-1):
		dist = positions[i+1]-positions[i]
		delta = [(colors[i+1][j] - colors[i][j])/dist for j in range(3)]
		for q in range(dist):
			grad[rainbowIdx] = [colors[i][j] + (delta[j]*q) for j in range(3)]
			rainbowIdx += 1
	return grad

def generateEvenGradient(colors, length):
	positions = [int(length * (i / (len(colors)-1))) for i in range(len(colors))]
	return generateGradient(colors, positions)

def generateBrightColor(otherColor=[0,0,0]):
	color = [0, 0, 0]
	while color == [0, 0, 0] or color == otherColor:
		color = [random.randint(0, 1)*led_brightness.LED_FULL_BRIGHT, random.randint(0, 1)*led_brightness.LED_FULL_BRIGHT, random.randint(0, 1)*led_brightness.LED_FULL_BRIGHT]
	return color

class gradients:
	RAINBOW = generateEvenGradient([[0, 255, 0], [165, 255, 0], [255, 255, 0], [255, 0, 0], [0, 0, 255], [0, 75, 130], [0, 139, 255], [0, 255, 0]], int(leds.numLeds * 7 / 6))
	RBG = generateEvenGradient([colors.RED, colors.BLUE, colors.GREEN, colors.RED], leds.numLeds)
	GBR = generateEvenGradient([colors.GREEN, colors.BLUE, colors.RED, colors.GREEN], leds.numLeds)
	GRB = generateEvenGradient([colors.GREEN, colors.RED, colors.BLUE, colors.GREEN], leds.numLeds)
	RGB = generateEvenGradient([colors.RED, colors.GREEN, colors.BLUE, colors.RED], leds.numLeds)
	BRG = generateEvenGradient([colors.BLUE, colors.RED, colors.GREEN, colors.BLUE], leds.numLeds)
	BGR = generateEvenGradient([colors.BLUE, colors.GREEN, colors.RED, colors.BLUE], leds.numLeds)
	RB_STRIPE = generateEvenGradient([colors.RED, colors.BLUE], 2)
	RG_STRIPE = generateEvenGradient([colors.RED, colors.GREEN], 2)
	BG_STRIPE = generateEvenGradient([colors.BLUE, colors.GREEN], 2)

class gradient_list:
	ALL = [attr for attr in dir(gradients) if not callable(getattr(gradients, attr)) and not attr.startswith("__")]
