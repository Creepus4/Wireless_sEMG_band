import pyqtgraph as pg
from pyqtgraph.Qt import QtCore
from collections import deque
from plot_recorded_data_layout import setup_gui
import config
import numpy as np
from wrapper import write, read, createWaveletObj, deleteObj, pushData, transform
import json
import scipy.io 
import os

_base = os.path.dirname(os.path.abspath(__file__))
### unpack data and save in buffer ###
def store_data(data):    
    buffer = [deque() for _ in range(config.N_CHANNELS)]

    header = np.uint16(32896)

    sample_counter = 0            
    for val in data: 
        
        if val == header:
            continue
        
        buffer[sample_counter % config.N_CHANNELS].append(val) #add to target deque  
        sample_counter += 1  
    print(f'data i buffer ch1 {len(buffer[0])}')
    print(f'data i buffer ch2 {len(buffer[1])}')          
    return buffer

### unpack data and plot (the plots in this file is not the main thing) ###
def update_reading():

    global mat_index, buffer, hm, cwt_plot, interesting_freq, raw_buffers, t_index
    global alpha, contr_data_rms, contr_data_cwt, ext, is_running
    if not is_running:
        return
    new_data_recieved = False
    
    num_to_proc = min(min(len(x) for x in buffer), 2000)
    
    if num_to_proc <= 0:
        # print(f'ch1 cwt: {np.max(contr_data_cwt[0])}')
        # print(f'ch2 cwt: {np.max(contr_data_cwt[1])}')
        # print(f'ch3 cwt: {np.max(contr_data_cwt[2])}')
        if ext:
            with open(os.path.join(_base, 'LDA_extension_data.json'), 'w') as f:
                json.dump({'contr_data_rms' : contr_data_rms, 'contr_data_cwt': contr_data_cwt}, f)
        else:
            with open(os.path.join(_base, 'LDA_flexion_data.json'), 'w') as f:
                json.dump({'contr_data_rms' : contr_data_rms, 'contr_data_cwt': contr_data_cwt}, f)    
        return
    
    for _ in range(num_to_proc):
        for ch in range(config.N_CHANNELS):

            raw_val = buffer[ch].popleft()
            v_raw = np.float32(config.BIT_TO_VOLTS * raw_val)
            
        
            dc_offset[ch] = np.float32(alpha * dc_offset[ch]) + ((1 - alpha) * v_raw) #update estimated dc offset
            voltage = np.float32(v_raw - dc_offset[ch])
            pushData(voltage,ch)
            raw_buffers[ch].append(voltage) # raw sEMG data
                
            rms_val, rms_calc_buffers[ch], rms_sums[ch] = rms(voltage, rms_calc_buffers[ch], rms_sums[ch])
            rms_buffers[ch].append(rms_val if rms_val is not None else 0.0)
                
            if rms_val is not None:
                #heatmap
                hm_data[ch, :-1] = hm_data[ch, 1:]
                hm_data[ch, -1] = rms_val
                new_data_recieved = True  
                    
            if ch == 0:
                    cur_win.append(voltage)
                    
                    cur_time = t_index/config.Fs
                    time_axis.append(cur_time)
                    t_index += 1 
        
        #cwt    
        if len(raw_buffers[0]) >= config.N and t_index % 50 == 0:
              
                for ch in range(config.N_CHANNELS):
                    
                    transform(cwt,ch)
                    ch_avg_cwt = np.mean(cwt[:, interesting_freq])
                    contr_data_cwt[ch].append(float(ch_avg_cwt))
                    
                    curr_rms = rms_buffers[ch][-1]
                    contr_data_rms[ch].append(float(curr_rms))
                    
                    if ch == 0:

                        cwt_plot.setImage(cwt, levels = (-20,20), autoLevels=False)
        mat_index += 1             
       
    time_data = np.array(time_axis)
    for i in range(config.N_CHANNELS):
        raw_data = np.array(raw_buffers[i])
        rms_data = np.array(rms_buffers[i])
        
        min_len = min(len(time_data), len(raw_data))
        curves[i].setData(time_data[:min_len], raw_data[:min_len])
        
        min_len_rms = min(len(time_data), len(rms_data))
        curves[i+config.N_CHANNELS].setData(time_data[:min_len_rms], rms_data[:min_len_rms])
        
    for i in range(len(plots)):
        plots[i].setXRange(cur_time - (config.WINDOW_SIZE / config.Fs), cur_time, padding = 0) #set out data for raw/rms plots
    if new_data_recieved:
        hm.setImage(hm_data.T, autoLevels=False)
        
### calculate RMS ###        
def rms(sample, rms_buffer, rms_sum):
    
    if len(rms_buffer) == config.N:
        old = rms_buffer[0]
        rms_sum -= old**2
        
    rms_buffer.append(sample)
    rms_sum += abs(sample)**2
    
    if len(rms_buffer) == config.N:
        return np.sqrt((rms_sum / config.N)), rms_buffer, rms_sum
    else:
        return None, rms_buffer, rms_sum

### perform necessary CWT preparations ###
def cwt_prep():
    
    freq_vector = np.logspace(np.log10(10), np.log10(500), config.FREQ, dtype=np.float32)
    cwt = np.asfortranarray(np.zeros((config.N, freq_vector.size), dtype=np.float32))
    createWaveletObj(freq_vector, config.N, config.Fs)
    interesting_freq = np.where((freq_vector >= 20) & (freq_vector <= 450))[0] #frequencies to study for LDA

    return cwt, interesting_freq

### start/stop button ###
def on_toggle():
    
    global rms_buffers, raw_buffers, is_running
    is_running = not is_running
    
    if is_running:
        btn_start.setText("Stop Measurement")
        # Clear old data in serial port before starting
        timer.start(20)
        
    else:
        btn_start.setText("Start Measurement")
        timer.stop()
        cur_win.clear()

        for i in range(config.N_CHANNELS):
                buffer[i].clear()
                raw_buffers[i].clear()
                rms_buffers[i].clear()
  
          
if __name__ == '__main__':
    is_running = False
    ext = False
    
    
    if ext:
        ## extension file ##
        ext_file = os.path.join(_base, 'EMGData_wrist_extension.mat')
        mat_data = scipy.io.loadmat(ext_file)
            
    else:
        ## flexion file ##
        flex_file = os.path.join(_base, 'EMGData_wrist_flexion.mat')
        mat_data = scipy.io.loadmat(flex_file)
    
    
    data = mat_data['saveData'].flatten()
    print(data[:-200])
    data = np.array(data, dtype=np.uint16)

    found_headers = np.sum(data == 32896)
    print(f"Hittade {found_headers} möjliga header-sekvenser i den råa byteströmmen.")
    
    ## buffer read data ##
    buffer =  store_data(data)   
    
    ## set up gui ##
    curves, hm, cwt_plot, main_win, btn_start, plots = setup_gui()
    
    # preparation heatmap
    hm_data = np.zeros((config.N_CHANNELS, config.HISTORY))
    
    # preparation cwt
    cwt, interesting_freq = cwt_prep()
    
    # preparation rms
    fft_buffer = deque(maxlen=config.N)
    cur_win = deque(maxlen=config.N)
    alpha = 0.95
    
    rms_sums = [0.0] * config.N_CHANNELS
    dc_offset = [1.65] * config.N_CHANNELS 
    
    rms_buffers = [deque(maxlen=config.WINDOW_SIZE) for _ in range(config.N_CHANNELS)]
    rms_calc_buffers = [deque(maxlen=config.N) for _ in range(config.N_CHANNELS)]
    raw_buffers = [deque(maxlen=config.WINDOW_SIZE) for _ in range(config.N_CHANNELS)]
    
    time_axis = deque(np.zeros(config.WINDOW_SIZE, dtype=np.float32), maxlen=config.WINDOW_SIZE)
    t_index = 0

    ### ta emot data och spara data i deques (buffer) ###
    zeros_array = np.zeros(config.WINDOW_SIZE, dtype=np.float32)

    del zeros_array

    timer = QtCore.QTimer()
    timer.timeout.connect(update_reading)        
    timer.start(20)
    btn_start.clicked.connect(on_toggle)
    
    contr_data_rms = [[] for _ in range(config.N_CHANNELS)]
    contr_data_cwt = [[] for _ in range(config.N_CHANNELS)]
    
    ext_data_cwt = [[] for _ in range(config.N_CHANNELS)]
    ext_data_rms = [[] for _ in range(config.N_CHANNELS)]
    
    all_cwt_res = 0
    mat_index = 0
    
    
    pg.exec() 
    
