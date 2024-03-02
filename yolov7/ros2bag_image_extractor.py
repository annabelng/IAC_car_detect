# ---------------------------------------------------------------------------- #
#                                    Imports                                   #
# ---------------------------------------------------------------------------- #

# ------------------------- System related Libraries ------------------------- #
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
from utils_detect import detect

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
def detect_objects(opt, cv_img, path):
    num_cars = detect(opt, cv_img,path)
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

arg_parser.add_argument('--weights', nargs='+', type=str, default='yolov7/runs/best.pt', help='model.pt path(s)')
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
arg_parser.add_argument('--no-trace', action='store_true', help='don`t trace model')

# ------------------------------ Parse Arguments ----------------------------- #
args = arg_parser.parse_args()

OUTPUT_DIR  = args.output_dir

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
        '/vimba_rear_left/image/compressed',       
        '/vimba_rear_right/image/compressed',   
        '/vimba_rear_left/image'            ,
        '/vimba_rear_right/image'           ,
        '/vimba_front_left/image'           ,
        '/vimba_front_left_center/image'    ,
        '/vimba_front_right_center/image'   ,
        '/vimba_front_right/image'          
    }
else:
    image_topics = {
        '/vimba_rear_left/image'            ,
        '/vimba_rear_right/image'           ,
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

while reader.has_next():
    
    # Read the next message
    topic_name, data, timestamp = reader.read_next()
    
    if topic_name in iterator.keys():
        # Update iterator for this topic
        iterator[topic_name] += 1

        # Extract message from rosbag
        msg_type = TYPE_MAP[topic_name]
        msg_ser = get_message(msg_type)
        msg = deserialize_message(data, msg_ser)
        output_topic = None
        if (args.compressed and msg_type == "sensor_msgs/msg/CompressedImage"):
            np_arr = np.frombuffer(msg.data, np.uint8)
            cv2_msg = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
            output_topic = topic_name[7:-17]
        else:
            # Convert to cv2 image
            cv2_msg = bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
            output_topic = topic_name[1:-6]

        # Create a directory for topic in output dir if it does not exist
        # print("Output Topic: ", output_topic)
        output_directory = os.path.join(OUTPUT_DIR, output_topic)
        
        if not os.path.exists(output_directory):
            if args.verbose:
                print("Creating Directory: ", output_directory)
            os.mkdir(output_directory)

        output_file_path = os.path.join(output_directory, 'Image' + '_' + '{0:010d}'.format(iterator[topic_name]) + '_' + str(msg.header.stamp.sec) + '_' + str(msg.header.stamp.nanosec) + '.jpg')
        #print(output_file_path)
        # Undistort Image before Saving
        if args.undistort:
            # If distortion parameters not loaded then load them once
            if topic_name[1:-6] not in distortion_dict:
                yaml_file_path = args.camera_info_path + topic_name[1:-6] + '.yaml'
                try:
                    distortion_fp = open(file_path(yaml_file_path))
                except:
                    del reader
                    print("[script] FATAL ERROR: Opening .yaml file failed. NOT A FILE")
                    exit()
                distortion_dict[topic_name[1:-6]] = yaml.safe_load(distortion_fp)
            cv2_msg = undistort(cv2_msg, distortion_dict[topic_name[1:-6]])

        # Run detection on every twentieth image
        if counter % 20 == 0:
            detection_output = detect_objects(args, cv2_msg, output_file_path)
            cars_count += detection_output
            
            if detection_output == 1 and counter % 20 == 0:
                if not cv2.imwrite(output_file_path, cv2_msg):
                    raise Exception("Could not write image")
        counter += 1
        # print(counter)

        # Save Image
        if args.verbose:
            print('Saving ' + output_file_path)
        
        if counter % 100 == 0:
            print(f"Processed {counter} Images")

        if cars_count % 50 == 0 and cars_count > 0:
            print(f"Processed cars {cars_count} Images")

# check counters
print("OUT OF LOOP")
counter = counter / 5
print("final car count is ", cars_count)
print("final image count is ", counter)

# calculate percentage 
if cars_count / counter > 0.02:
    # Write the rosbag file path to a text file
    with open("car_rosbag_paths.txt", "a") as file:
        file.write(ROSBAG_FILE_PATH + "\n")
    print("ROSBAG CONTAINS CARS")

# Close the bag file
del reader