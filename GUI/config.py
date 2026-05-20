PORT = 'COM3' # the port which the ESP is connected to
BAUD = 921600 # baud rate
WINDOW_SIZE = 20000 # window len for rms
BIT_TO_VOLTS = 3.3 / 4095
TIMEOUT = 0.0
YRANGE_p1 = 2 # yrange plot
YRANGE_p2 = 1 # yrange plot
N = 512 # need to be 2^x (256, 512, ...)

N_CHANNELS = 3 # number of channels
HM_HISTORY = 20000 # window length for heatmap
Fs = 2000   # sampling freq 2000Hz

FREQ = 60 # number of frequencies

# levels CWT
min_level_cwt, max_level_cwt = 0, 200
# levels heatmap
min_level_hm, max_level_hm = 0, 1