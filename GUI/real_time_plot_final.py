import os
os.environ['PYQTGRAPH_QT_LIB'] = 'PyQt5' #due to bugs in the GUI related to PyQt6
import pyqtgraph as pg
from pyqtgraph.Qt import QtCore
import serial
import struct
from collections import deque
from real_time_plot_layout_final import setup_gui
import config
import numpy as np
import time
import threading
from wrapper import createWaveletObj, pushData, transform
from LDA_collect_data_prettier_version import classify, load_models
import scipy.io as scipy

#flags
is_running = False
classification_enabled = False #press button to activate classification

### unpack data and plot (if connected = True) ###
def serial_reader():
    
    global header, header_size, sample_counter
    
    while True:
        if ser.in_waiting >= 194:
            
            res = ser.read(header_size)
            res_data = struct.unpack('<H', res)
            
            if res_data != header:
                ser.read(1)
                continue
            
            raw = ser.read(data_size)
            values = struct.unpack(f'<{data_size //2}H', raw) #unpack bits
            sample_counter = 0
            
            for val in values: 
                serial_buffers[sample_counter % config.N_CHANNELS].append(val) #add to target deque 
                sample_counter += 1
        else:
            time.sleep(0.001)

### generates dummy data when not connected to armband (if connected = False) ###          
def dummy_serial_reader():
    global t_sim
    fs = 2000
    f_signal = 50
    amplitude = 1.0
    offset = 1.65
    t_sim = 0

    while True:
        t_vals = t_sim + np.arange(32) / fs
        volt_vals = offset + amplitude * np.sin(2 * np.pi * f_signal * t_vals)
        adc_vals = np.round(volt_vals * 4095.0 / 3.3).astype(np.uint16)
            
        for ch in range(config.N_CHANNELS):
            for val in adc_vals:
                serial_buffers[ch].append(int(val))
            
        t_sim += 32 / fs
        time.sleep(0.02)
            
### unpack and plot data ###
def update():
    if not is_running:
        return

    global alpha, dc_offset, t_index, serial_buffers, new_data_recieved
    global rms_sums, rms_buffers, interesting_freq, record, oscillation
    
    if any(len(y) < 32 for y in serial_buffers): #if less than 32 values, return and wait for more values
        return
    
    num_to_proc = min(min(len(x) for x in serial_buffers), 2000)
    cur_time = 0
    new_data_recieved = False
    for ch in range(config.N_CHANNELS):
     
        value = np.fromiter((serial_buffers[ch].popleft() for _ in range(num_to_proc)),dtype=np.uint16) #get all available values (max 2000)

        raw = np.float32(config.BIT_TO_VOLTS * value) #scaled sample

        for i in raw:
            dc_offset[ch] = np.float32(alpha * dc_offset[ch] + ((1 - alpha) * i)) #update estimated dc offset
            
            voltage = np.float32(i - dc_offset[ch]) #scaled sample without offset

            pushData(voltage,ch) #pushing voltage for CWT calculations
            raw_buffers[ch].append(voltage)
            rms_val, rms_calc_buffers[ch], rms_sums[ch] = rms(voltage, rms_calc_buffers[ch], rms_sums[ch])
            
            rms_buffers[ch].append(rms_val if rms_val is not None else 0.0)
            
            if rms_val is not None:
                #heatmap
                hm_data[ch, :-1] = hm_data[ch, 1:]
                hm_data[ch, -1] = rms_val
                new_data_recieved = True  
                
            target_ch = 0 if current_mode == 0 else (current_mode - 1)
            if ch == target_ch: 
                cur_win.append(voltage)
                
                cur_time = t_index/config.Fs
                time_axis.append(cur_time)
                t_index += 1      

    #cwt    
    if len(cur_win) >= config.N and t_index % 50 == 0:
        
        classify_data_rms = []
        classify_data_cwt = []
            
        #movement classification
        for ch in range(config.N_CHANNELS) :
                
            if classification_enabled and t_index % 50 == 0:
                curr_rms = rms_buffers[ch][-1]
                classify_data_rms.append(curr_rms)
                    
                transform(cwt,ch)
                ch_avg_cwt = np.mean(cwt[ : , interesting_freq]) 
                classify_data_cwt.append(ch_avg_cwt)

                if len(classify_data_rms) == config.N_CHANNELS and len(classify_data_cwt) == config.N_CHANNELS:
                        input_data = classify_data_rms + classify_data_cwt
                        movement = classify(input_data)
                        value_label.setText(f'{movement}')
            target_ch = 0 if current_mode == 0 else (current_mode - 1)    
            if ch == target_ch and not classification_enabled and t_index % 50 == 0: #plottar endast en kanal åt gången
                transform(cwt, ch)
                 
        cwt_plot.setImage(cwt, autoLevels=False)
        cwt_width = config.N / config.Fs
        cwt_plot.setRect(pg.QtCore.QRectF(cur_time - cwt_width * 1, 0, cwt_width, config.FREQ))
        p_cwt.setXRange(cur_time - cwt_width, cur_time, padding = 0)        
            
    #plot raw data and rms
    time_data = np.array(time_axis)
    for i in range(config.N_CHANNELS):
        raw_data = np.array(raw_buffers[i])
        rms_data = np.array(rms_buffers[i])
        
        min_len = min(len(time_data), len(raw_data))
        curves[i].setData(time_data[:min_len], raw_data[:min_len])
        
        min_len_rms = min(len(time_data), len(rms_data))
        curves[i+config.N_CHANNELS].setData(time_data[:min_len_rms], rms_data[:min_len_rms])
        
    for i in range(len(plots)):
        plots[i].setXRange(cur_time - (config.WINDOW_SIZE / config.Fs), cur_time, padding = 0)

    if new_data_recieved: #plot rms in heatmap

        hm.setImage(hm_data.T, autoLevels=False) 
        hm_width = config.HM_HISTORY / config.Fs
        hm.setRect(pg.QtCore.QRectF(cur_time - hm_width, 0, hm_width, config.N_CHANNELS))
        p_hm.setXRange(cur_time - hm_width, cur_time, padding = 0)

### start/stop button ###    
def on_toggle():

    global rms_buffers, raw_buffers, is_running, t_sim
    is_running = not is_running
    
    if is_running:
        t_sim = 0
        btn_start.setText("Stop Measurement")
        
        if connected:
            ser.reset_input_buffer() #Clear old data in serial port before starting
        timer.start(20)
        
    else:
        btn_start.setText("Start Measurement")
        timer.stop()
        cur_win.clear()
        
        for i in range(config.N_CHANNELS):
                serial_buffers[i].clear()
                raw_buffers[i].clear()
                rms_buffers[i].clear()

### toggle classification ###                
def update_classification_flag():
    global classification_enabled
    
    classification_enabled = btn_classify.isChecked()

### toggle view ###    
def change_view_reset(mode):
    global current_mode
    
    current_mode = mode #update selected view
    
    toggle_view(mode)
    
    cur_win.clear()

### calculate RMS ###    
def rms(sample, rms_buffer, rms_sum):
    
    if len(rms_buffer) == config.N:
        old = rms_buffer[0]
        rms_sum -= old**2
        
    rms_buffer.append(sample)
    rms_sum += abs(sample)**2
    
    if len(rms_buffer) == config.N: #when buffer is filled, calculate RMS value

        return np.sqrt(rms_sum / config.N), rms_buffer, rms_sum
    else:
        return None, rms_buffer, rms_sum   

### perform necessary CWT preparations ###    
def cwt_prep():
    
    freq_vector = np.logspace(np.log10(10), np.log10(500), config.FREQ, dtype=np.float32) #frequencies to study in CWT, higher resolution in low freq
    cwt = np.asfortranarray(np.zeros((config.N, freq_vector.size), dtype=np.float32))
    createWaveletObj(freq_vector, config.N, config.Fs)
    interesting_freq = np.where((freq_vector >= 20) & (freq_vector <= 450))[0] #frequencies to study for LDA

    return cwt, interesting_freq

if __name__ == '__main__':
    #simulation prep
    sinus = True
    t_sim = 0

    #header data
    header = np.uint16(32896) # depend on set header/sync word in ESP transmitter code
    header_size = 2 
    data_size = 194 - header_size
    sample_counter = 0
    
    #time axis
    time_axis = deque(np.zeros(config.WINDOW_SIZE, dtype=np.float32), maxlen=config.WINDOW_SIZE)
    t_index = 0
    
    #setup GUI
    app, curves, hm, cwt_plot, main_win, btn_start, plots, value_label, btn_classify, btn_all_plots, btn_ch1_all, btn_ch2_all ,btn_ch3_all, toggle_view, p_cwt, p_hm = setup_gui()

    # lists of deques depending on num channels
    serial_buffers = [deque(maxlen=config.WINDOW_SIZE) for _ in range(config.N_CHANNELS)]
    raw_buffers = [deque(maxlen=config.WINDOW_SIZE) for _ in range(config.N_CHANNELS)]
    rms_buffers = [deque(maxlen=config.WINDOW_SIZE) for _ in range(config.N_CHANNELS)]
    rms_calc_buffers = [deque(maxlen=config.N) for _ in range(config.N_CHANNELS)]
    rms_sums = [0.0] * config.N_CHANNELS
    
    connected = True
    if connected:
        ser = serial.Serial(port=config.PORT, baudrate=config.BAUD, timeout=config.TIMEOUT, write_timeout=0)
        threading.Thread(target = serial_reader, daemon=True).start()
    else:
        threading.Thread(target=dummy_serial_reader, daemon=True).start()


    #offset estimation
    dc_offset = [1.65] * config.N_CHANNELS 
    alpha = 0.99
    
    # preparation heatmap
    hm_data = np.zeros((config.N_CHANNELS, config.HM_HISTORY )) #config.HISTORY
    
    # preparation cwt
    cwt, interesting_freq = cwt_prep()
    
    # preparation rms
    cur_win = deque(maxlen=config.N)

    #buttons
    btn_classify.clicked.connect(update_classification_flag)
    btn_start.clicked.connect(on_toggle)
    
    #view buttons
    current_mode = 0 # what view is shown first, 0 = All
    toggle_view(0) #view 0 as standard view
    btn_all_plots.clicked.connect(lambda: change_view_reset(0))
    btn_ch1_all.clicked.connect(lambda:change_view_reset(1))
    btn_ch2_all.clicked.connect(lambda:change_view_reset(2))
    btn_ch3_all.clicked.connect(lambda:change_view_reset(3))
    
    #load LDA models
    load_models()
    
    #GUI updates
    timer = QtCore.QTimer()
    timer.timeout.connect(update)
    
    pg.exec() 
