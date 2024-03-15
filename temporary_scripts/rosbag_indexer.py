import os
import sqlite3
import yaml

# ----------------------- ENVIRONMENT VARIABLES LOADING ---------------------- #
# Path to the .env file (one folder above the current directory)
root_folder = os.path.join(os.path.dirname(__file__), '..')

# Load variables from .env file
env_vars = load_env_variables()
# ---------------------------------------------------------------------------- #

def process_rosbag(rosbag_path):
    """
    Placeholder function for processing ROSBAG to obtain metadata.
    Replace this function's body with your actual processing code.
    """
    # Example return values
    return 3600, 25.0, 10000, 2500  # TotalLength, PercentageCarImages, TotalImages, TotalCarImages

def insert_rosbag_metadata(conn, rosbag_metadata):
    """
    Insert a new row into the RosbagMetadata table.
    """
    sql = ''' INSERT INTO RosbagMetadata(RosbagFolderPath,TotalLength,PercentageCarImages,TotalImages,TotalCarImages,IsBroken)
              VALUES(?,?,?,?,?,?) '''
    cur = conn.cursor()
    cur.execute(sql, rosbag_metadata)
    conn.commit()

def find_and_process_rosbags(root_folder):
    """
    Find ROSBAG paths under root_folder that match the criteria and process them.
    """
    database = os.path.join(root_folder, env_vars["ROSBAG_DATABASE_PATH"])
    conn = sqlite3.connect(database)  # Connect to your database
    for subdir, dirs, files in os.walk(root_folder):
        has_db3 = any(file.endswith('.db3') for file in files)
        has_mcap = any(file.endswith('.mcap') for file in files)
        has_metadata = 'metadata.yaml' in files
        
        if has_db3 and has_mcap and has_metadata:
            try:
                total_length, percentage_car_images, total_images, total_car_images = process_rosbag(subdir)
                insert_rosbag_metadata(conn, (subdir, total_length, percentage_car_images, total_images, total_car_images, False))
            except Exception as e:
                print(f"Error processing ROSBAG in {subdir}: {e}")
        elif has_db3 and has_mcap and not has_metadata:
            insert_rosbag_metadata(conn, (subdir, None, None, None, None, True))

if __name__ == '__main__':
    find_and_process_rosbags("path_to_your_root_folder")