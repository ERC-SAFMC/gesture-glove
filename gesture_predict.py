# gesture_predict.py
# Description:   
# Written by: harwHarw03
# Created on January 13th 2024

import numpy as np 
import pandas as pd 
import datetime
import re
import os, os.path
import time
import random
import tensorflow as tf
import serial

PORT = "/dev/ttyUSB0"
#PORT = "/dev/ttyUSB1"
#PORT = "COM8"

serialport = None
serialport = serial.Serial(PORT, 115200, timeout=0.05)

#load Model
model = tf.keras.models.load_model('model.h5')

def get_imu_data():
    global serialport
    if not serialport:
        serialport = serial.Serial(PORT, 115200, timeout=0.05)
        print("Opened", serialport.name)
        time.sleep(3)
        serialport.readline()

    line = str(serialport.readline(),'utf-8')
    if not line:
        return None
 
    vals = line.replace("Uni:", "").strip().split(',')
 
    if len(vals) != 7:
        return None
    try:
        vals = [float(i) for i in vals]
    except ValueError:
        return ValueError
 
    return vals

def reshape_function(data):
    reshaped_data = tf.reshape(data, [-1, 3, 1])
    return reshaped_data

""" 
def data_pipeline(data_a):
    tensor_set = tf.data.Dataset.from_tensor_slices((data_a[:,:,1:4]))
    tensor_set_cnn = tensor_set.map(reshape_function)
    tensor_set_cnn = tensor_set_cnn.batch(192)
    return tensor_set_cnn
 """
def gesture_Handler(sock, rw, data, dataholder, dataCollecting, gesture, old_gesture):
    dataholder = np.array(get_imu_data())
    if dataholder.all() != None:
        #print(dataholder)
        dataCollecting = True
        data[0, rw, :] = dataholder
        rw += 1
        if rw > 380:
            rw = 380
    if dataholder.all() == None and dataCollecting == True:
        if rw == 380:
            prediction = np.argmax(model.predict(data_pipeline(data)), axis=1)
            gesture=gest_id[prediction[0]]
        rw = 0
        dataCollecting = False
    return rw, gesture, old_gesture, dataCollecting


if __name__ == "__main__":
    gest_id = {0:'forward', 1:'backward', 2:'', 3:'right', 4:'left'}#, 5:'up'}#, 6:'down'}
    data = np.zeros(shape=(1,380,7))
    dataholder = np.zeros(shape=(1,7))
    row = 0
    dataCollecting = False
    gesture = ''
    old_gesture = ''

    time.sleep(3)
    serialport.readline()

    while(1):
        t=time.time()
        row, gesture, old_gesture, dataCollecting = gesture_Handler(sock,row,data,dataholder,dataCollecting,gesture,old_gesture)
        if gesture != old_gesture:
            print(gesture)    
            old_gesture=gesture
        