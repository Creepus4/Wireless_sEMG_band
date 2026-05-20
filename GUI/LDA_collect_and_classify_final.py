import numpy as np
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
from sklearn.preprocessing import StandardScaler 
import numpy as np
import json   
import joblib
import os

scaler = StandardScaler()
lda_model = None
base_path = os.path.dirname(__file__)

## load created model ##   
def load_models():
    global lda_model, scaler
    try:
        lda_model = joblib.load(os.path.join(base_path, 'lda_model_2.pkl'))
        scaler = joblib.load(os.path.join(base_path, 'scaler_2.pkl'))
        print('LDA models found')
    except:
        print('LDA models missing')
    
## splits up the values for each channel, stacked_values[0] corresponds to channel 1 ##   
def stack_ch(list): 
    
    length = len(min(list, key = len))  #to assure equal distribution of values in case of uneven amount of data
    stacked_values = np.vstack([np.array(x[:length]) for x in list])

    return stacked_values

## creates training data ##
def training_data(flexion_data, extension_data):
    
    global scaler
    
    rms_data_flex = stack_ch(flexion_data['contr_data_rms'])
    cwt_data_flex = stack_ch(flexion_data['contr_data_cwt'])
    
    rms_data_ext = stack_ch(extension_data['contr_data_rms'])
    cwt_data_ext = stack_ch(extension_data['contr_data_cwt'])
    
    rms_thres_arr = np.array([0.3731, 0.0934, 0.4593]) * 1.1 #calibrate threshold using static multiplier
    cwt_thres_arr = np.array([99.0934, 30.3261, 106.6445]) * 1.5 #calibrate threshold using static multiplier
    
    ext_labels = create_labels(rms_data_ext, cwt_data_ext, rms_thres = rms_thres_arr, cwt_thres = cwt_thres_arr, id = 1)
    flex_labels = create_labels(rms_data_flex, cwt_data_flex, rms_thres = rms_thres_arr, cwt_thres = cwt_thres_arr, id = 2)
    
    print(f'flex: {flex_labels}') #tip is to make sure to have en even distribution of 2 and 0
    print(f'ext: {ext_labels}') #tip is to make sure to have en even distribution of 1 and 0
    
    Y = np.hstack([ext_labels, flex_labels])

    X = np.vstack([np.hstack([rms_data_flex.T, cwt_data_flex.T]),
                   np.hstack([rms_data_ext.T, cwt_data_ext.T])])
    
    X_scaled = scaler.fit_transform(X)

    return X_scaled, Y

## create class labels, defines activation/rest based on set thresholds ##
def create_labels(rms_data, cwt_data, rms_thres, cwt_thres, id):
    
    rms_active_mask = rms_data >= rms_thres[:, np.newaxis]
    cwt_active_mask = cwt_data >= cwt_thres[:, np.newaxis]
    
    rms_any_active = np.any(rms_active_mask, axis= 0)
    cwt_any_active = np.any(cwt_active_mask, axis= 0)    

    activated = rms_any_active | cwt_any_active #if ANY is active it counts as active (bitwise OR)
    
    labels = np.where(activated, id, 0) #id for activation, 0 for rest

    return labels

## creates LDA model ##   
def calc_LDA(X, Y):

    lda_model = LinearDiscriminantAnalysis()
    lda_model.fit(np.array(X), np.array(Y))
    return lda_model

## classifies movement in real-time ##
def classify(data):
    global lda_model, scaler
    
    '''data consists of a 1D array with 2 values per channel:
        data = [RMS_ch1, RMS_ch2, mean_CWT_ch1, mean_CWT_ch2]
        has to be repacked as [[RMS_ch1, RMS_ch2, mean_CWT_ch1, mean_CWT_ch2]]'''
    
    if lda_model is None or scaler is None:
        return 'LDA model not initalized'
    
    data_2D = np.array(data).reshape(1, -1)
    scaled_data = scaler.transform(data_2D)
    
    prediction = lda_model.predict(scaled_data)[0]
    
    ## could use a majority vote here
    mapping = {0: 'Resting', 1: 'Wrist extension', 2: 'Wrist flexion' }
    
    return mapping.get(prediction, 'Unknown')
    

if __name__ == '__main__':
    
    
    try:
        with open(r'Z:/Åk3/Kandidatarbete/Python/Recorded data/LDA_flexion_data.json', 'r') as f: #get processed flexion data
            flexion_data = json.load(f)
            
        with open(r'Z:/Åk3/Kandidatarbete/Python/Recorded data/LDA_extension_data.json', 'r') as f: #get processed extension data
            extension_data = json.load(f)        
        
        X, Y = training_data(flexion_data, extension_data)
        lda_model = calc_LDA(X, Y)

        joblib.dump(lda_model, os.path.join(base_path,'lda_model_2.pkl') )
        joblib.dump(scaler, os.path.join(base_path,'scaler_2.pkl'))
        
        print('LDA models created')
    except:
        print('JSON files with LDA models not found')
    
    
    