import os
import sys
import argparse
import yaml
import subprocess

# ----------------------------- Common Libraries ----------------------------- #
import numpy as np
import cv2

# --------------------------- ROS related Libraries -------------------------- #
from cv_bridge import CvBridge

import rosbag2_py

from rclpy.serialization import deserialize_message
from rosidl_runtime_py.utilities import get_message


# Now you can import the modules from the yolov7 folder
#from utils_detect import detect
from onnx_inference import detect, letterbox
from temporary_scripts.utils import load_env_variables
from create_database import insert_entry, create_connection

# ---------------------------------------------------------------------------- #
#                                   Functions                                  #
# ---------------------------------------------------------------------------- #

# ------------------------ Check if directory is valid ----------------------- #
def dir_path(string):
    print(string)
    if os.path.isdir(string):
        print(f"Is a directory! {string}")
        return string
    else:
        print(f"Is not a directory! {string}")
        raise NotADirectoryError(string)

# ----------------------- Check if file path is valid ----------------------- #
def file_path(string):
    if os.path.isfile(string):
        # print(f"Is a file! {string}")
        return string
    else:
        # print(f"Is not a string! {string}")
        raise FileNotFoundError(string)

# ------------------------------ Undistort Image ----------------------------- #
def undistort(input, distortion_data):
    # Extract Camera Matrix
    camera_matrix = np.array(distortion_data['camera_matrix']['data'])
    camera_matrix = np.reshape(camera_matrix, (distortion_data['camera_matrix']['rows'], distortion_data['camera_matrix']['cols']))
    
    # Extract Distortion Matrix
    distortion_matrix = np.array(distortion_data['distortion_coefficients']['data'])

    # Undistort and Return
    return cv2.undistort(input, camera_matrix, distortion_matrix)

# ------------------------------ Car Detection with YOLO ----------------------------- #
def detect_objects(cv_img, weights_path, output_file_path):
    num_cars = detect(cv_img, weights_path, output_file_path)
    return num_cars

# ---------------------------------------------------------------------------- #
#                           Setup & Argument Handling                          #
# ---------------------------------------------------------------------------- #
arg_parser  = argparse.ArgumentParser(description='Extracts Images from ROS2 Bags')

# ------------------------------- Add Arguments ------------------------------ #
arg_parser.add_argument('rosbag_file_path', help='Path to rosbag to extract the data from', type=dir_path)
arg_parser.add_argument('output_dir', help='Path to directory where extracted data should be stored', type=dir_path)
arg_parser.add_argument('-u', "--undistort", action="store_true")
arg_parser.add_argument('-c', "--compressed", action="store_false")
arg_parser.add_argument('-p', '--camera_info_path', help="Path to folder containing yaml config files for camera info for all cameras", type=dir_path)
arg_parser.add_argument('-v', "--verbose", action="store_true")

arg_parser.add_argument('--weights', nargs='+', type=str, default='yolov7/runs/best.onnx', help='model.pt path(s)')
"""
arg_parser.add_argument('--source', type=str, default='inference/images', help='source')  # file/folder, 0 for webcam
arg_parser.add_argument('--img-size', type=int, default=640, help='inference size (pixels)')
arg_parser.add_argument('--conf-thres', type=float, default=0.25, help='object confidence threshold')
arg_parser.add_argument('--iou-thres', type=float, default=0.45, help='IOU threshold for NMS')
arg_parser.add_argument('--device', default='', help='cuda device, i.e. 0 or 0,1,2,3 or cpu')
arg_parser.add_argument('--view-img', action='store_true', help='display results')
arg_parser.add_argument('--save-txt', action='store_true', help='save results to *.txt')
arg_parser.add_argument('--save-conf', action='store_true', help='save confidences in --save-txt labels')
arg_parser.add_argument('--nosave', action='store_false', help='do not save images/videos')
arg_parser.add_argument('--classes', nargs='+', type=int, help='filter by class: --class 0, or --class 0 2 3')
arg_parser.add_argument('--agnostic-nms', action='store_true', help='class-agnostic NMS')
arg_parser.add_argument('--augment', action='store_true', help='augmented inference')
arg_parser.add_argument('--update', action='store_true', help='update all models')
arg_parser.add_argument('--project', default='runs/detect', help='save results to project/name')
arg_parser.add_argument('--name', default='exp', help='save results to project/name')
arg_parser.add_argument('--exist-ok', action='store_true', help='existing project/name ok, do not increment')
arg_parser.add_argument('--no-trace', action='store_true', help='don`t trace model')"""

# ------------------------------ Parse Arguments ----------------------------- #
args = arg_parser.parse_args()

OUTPUT_DIR  = args.output_dir
WEIGHTS = args.weights

# Check if output directory exists
if os.path.exists(OUTPUT_DIR):
    # If it does exist, check if the directory is empty. If it is, just leave it. If not, just skip the rosbag.
    if os.listdir(OUTPUT_DIR):
        print("[script] Directory Exists and is Not Empty! Exiting...")
        exit()

print("[debug] Output Directory: ", OUTPUT_DIR)
ROSBAG_FILE_PATH = args.rosbag_file_path

"""if args.undistort:
    dir_path(args.camera_info_path)
    distortion_dict = dict() """

# --------------------------- Create ROS-CV Bridge --------------------------- #
bridge = CvBridge()

# ---------------------------------------------------------------------------- #
#                                  Main Script                                 #
# ---------------------------------------------------------------------------- #

# ---------------- Create reader instance and open for reading --------------- #
# with Reader(ROSBAG_FILE) as reader:
# Check if the extension is a db3 or mcap
files = os.listdir(ROSBAG_FILE_PATH)
print(f"[script] ROSBAG filepath: {ROSBAG_FILE_PATH}")
for file in files:
    if file.endswith(".db3"):
        store_type = "sqlite3"
        print("[script] Detected Input bag is a db3 file.")
        
    elif file.endswith(".mcap"):
        store_type = "mcap"
        print("[script] Detected Input bag is a mcap file.")
if not store_type:
    print(f"[script] FATAL ERROR: Input bag is not a db3 or mcap file")
    exit()

reader = rosbag2_py.SequentialReader()

# ----------------------------- OBTAIN ALL TOPICS ---------------------------- #
# Opens the bag files and sets the converter options
try:
    reader.open(
        rosbag2_py.StorageOptions(uri=ROSBAG_FILE_PATH, storage_id=store_type),
        rosbag2_py.ConverterOptions(
            input_serialization_format="cdr", output_serialization_format="cdr"
        ),
    )
except Exception as e:
    print(e)
    exit()


# Check if there are images in the ROSBAG, if not, skip!
# Get all the topic types and 
if args.compressed:

    image_topics = {
        '/vimba_front_left_center/image/compressed',
        '/vimba_front_right_center/image/compressed',
        '/vimba_front_left/image/compressed', 
        '/vimba_front_right/image/compressed',        
        #'/vimba_rear_left/image/compressed',       
        #'/vimba_rear_right/image/compressed',   
        #'/vimba_rear_left/image'            ,
        #'/vimba_rear_right/image'           ,
        '/vimba_front_left/image'           ,
        '/vimba_front_left_center/image'    ,
        '/vimba_front_right_center/image'   ,
        '/vimba_front_right/image'          
    }
else:
    image_topics = {
        #'/vimba_rear_left/image'            ,
        #'/vimba_rear_right/image'           ,
        '/vimba_front_left/image'           ,
        '/vimba_front_left_center/image'    ,
        '/vimba_front_right_center/image'   ,
        '/vimba_front_right/image'          
    }

TOPIC_TYPES = reader.get_all_topics_and_types()
TYPE_MAP = {TOPIC_TYPES[i].name: TOPIC_TYPES[i].type for i in range(len(TOPIC_TYPES))}

iterator = dict()

# Initialize an iterator based on whether or not the topic is in the rosbag
for t in TYPE_MAP:
    if t in image_topics:
        iterator[t] = 0

if len(iterator) == 0:
    print("[script] No Images to extract from this rosbag. Exiting...")
    # If no camera topics are found, close the ROSBAG and return. TODO: Check if ffmpeg is happy about this
    del reader
    exit()

counter = 0
cars_count = 0

# Function to create output directories for topics
def setup_output_directories(image_topics, output_dir):
    output_directories = {}
    for topic in image_topics:
        # Format the output topic directory name
        output_topic = topic[1:-6] if not args.compressed else topic[7:-17]
        output_directory = os.path.join(output_dir, output_topic)
        if not os.path.exists(output_directory):
            os.makedirs(output_directory, exist_ok=True)
            if args.verbose:
                print(f"Created directory: {output_directory}")
        output_directories[topic] = output_directory
    return output_directories

# Function to process and save a single message
def process_message(topic_name, data, msg_type):
    # Deserialize and convert the message to an OpenCV image
    msg_ser = get_message(msg_type)
    msg = deserialize_message(data, msg_ser)
    if args.compressed and msg_type == "sensor_msgs/msg/CompressedImage":
        np_arr = np.frombuffer(msg.data, np.uint8)
        cv_img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
    else:
        cv_img = bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')

    # Undistort the image if required
    if args.undistort:
        cv_img = undistort(cv_img, distortion_dict[topic_name[1:-6]])

    return cv_img

# Initialize output directories before processing messages
output_directories = setup_output_directories(image_topics, OUTPUT_DIR)

# Main processing loop
while reader.has_next():
    topic_name, data, timestamp = reader.read_next()

    if topic_name not in iterator:
        continue

    # Process message
    msg_type = TYPE_MAP[topic_name]
    cv_img = process_message(topic_name, data, msg_type)

    # Handling image detection and saving
    iterator[topic_name] += 1
    
    # Every 20th image (to reduce computation load), perform object detection on the image
    #if counter % 20 == 0:

    # Run detection every image
    detection_output = detect_objects(cv_img, WEIGHTS, output_file_path)
    cars_count += detection_output

    # Prepare output file path and save image
    output_directory = output_directories[topic_name]
    output_file_path = os.path.join(output_directory, f'Image_{iterator[topic_name]:010d}_{timestamp.sec}_{timestamp.nanosec}.jpg')
    if args.verbose:    
        print(f'Saving {output_file_path}')
    cv2.imwrite(output_file_path, cv_img)

    # Increment counters and print progress
    counter += 1
    if counter % 100 == 0 or cars_count % 50 == 0:
        print(f"Processed {counter} Images, Detected {cars_count} Cars")

percentage = cars_count / counter
# ----------------------------- INSERT INTO ROSBAG DATABASE ---------------------------- #

root_folder = os.path.join(os.path.dirname(__file__), '..')

# Load variables from .env file
env_vars = load_env_variables()
print(env_vars)

# Read path_to_your_database
rosbag_database = os.path.join(root_folder, env_vars["ROSBAG_DATABASE_PATH"])
print("Rosbag Database PATH:", rosbag_database)
rosbag_conn = create_connection(rosbag_database)

new_entry = (123456, ROSBAG_FILE_PATH, 1, percentage, counter, cars_count, 'Track XYZ', False, '2024-04-03', False, None)
insert_entry(new_entry)
rosbag_conn.close()

print("Inserted 1 database entry")
# -------------------------------------------------------------------------------------- #

# Final statistics and cleanup
print("Final car count is", cars_count)
print("Final image count is", counter)
if percentage > 0.05:
    with open("car_rosbag_paths.txt", "a") as file:
        file.write(f"{ROSBAG_FILE_PATH}\nTotal images (every 20): {counter}\nCar images (every 20): {cars_count}\n")
    print("ROSBAG CONTAINS CARS")

# Close the bag file
del reader