 
from everywhereml.data import Dataset
from everywhereml.data.collect import SerialCollector

"""
Create a SerialCollector object.
Each data line is marked by the 'IMU:' string
Collect 30 seconds of data for each gesture
Replace the port with your own!

If a imu.csv file already exists, skip collection
"""

imu_collector = SerialCollector(
    port='/dev/ttyUSB0', 
    baud=115200, 
    start_of_frame='IMU:', 
    feature_names=['ax', 'ay', 'az', 'gx', 'gy', 'gz', 'roll', 'pitch']
)
imu_dataset = imu_collector.collect_many_classes(
    dataset_name='ContinuousMotion', 
    duration=50
)
# save dataset to file for later use
imu_dataset.df.to_csv('imu.csv', index=False)
