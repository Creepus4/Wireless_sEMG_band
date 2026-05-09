PORT = 'COM3'
BAUD = 9216
WINDOW_SIZE = 20000 # Window length for rms ploy
BIT_TO_VOLTS = 3.3 / 4095
TIMEOUT = 0.0
YRANGE_p1 = 2
YRANGE_p2 = 1
N = 256 # Samples for CWT needs to be a power of 2

N_CHANNELS = 3 # Number of electrode channels
HISTORY = 100   # window len for cwt & heatmap

Fs = 2000   # sampeling frequnecy in Hz

FREQ = 60 # Number of frequencies for CWT