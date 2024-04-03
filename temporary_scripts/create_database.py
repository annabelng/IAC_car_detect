import sqlite3
from sqlite3 import Error
from dotenv import load_dotenv
import os
from utils import load_env_variables

def create_connection(db_file):
    """ create a database connection to a SQLite database """
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        print(sqlite3.version)
    except Error as e:
        print(e)
    finally:
        if conn:
            return conn

def create_table(conn, create_table_sql):
    """ create a table from the create_table_sql statement """
    try:
        c = conn.cursor()
        c.execute(create_table_sql)
    except Error as e:
        print(e)

def main():
    
    # Load variables from .env file
    # Path to the .env file (one folder above the current directory)
    root_folder = os.path.join(os.path.dirname(__file__), '..')

    # Load variables from .env file
    env_vars = load_env_variables()
    print(env_vars)
    
    # Read path_to_your_database
    rosbag_database = os.path.join(root_folder, env_vars["ROSBAG_DATABASE_PATH"])
    print("Rosbag Database PATH:", rosbag_database)

    image_database = os.path.join(root_folder, env_vars["IMAGE_DATABASE_PATH"])
    print("Image Database PATH:", image_database)

    sql_create_rosbag_metadata_table = """ CREATE TABLE IF NOT EXISTS RosbagMetadata (
                                        RosbagFolderPath TEXT PRIMARY KEY,
                                        TotalLength INTEGER NOT NULL,
                                        PercentageCarImages REAL NOT NULL,
                                        TotalImages INTEGER NOT NULL,
                                        TotalCarImages INTEGER NOT NULL,
                                        RacingTrackName TEXT,
                                        IsBroken BOOL NOT NULL,
                                        LastUpdated DATESTAMP NOT NULL,
                                        Missing BOOL NOT NULL,
                                        LastUpdatedBeforeMissing DATESTAMP
                                    ); """
    
    sql_create_image_metadata_table = """ CREATE TABLE IF NOT EXISTS ImageMetadata (
                                        ImageUniqueID INTEGER PRIMARY KEY,
                                        XPosOfCar INTEGER,
                                        YPosOfCar INTEGER,
                                        TotalImages INTEGER,
                                        TotalCarImages INTEGER,
                                        WidthOfCar INTEGER,
                                        HeightOfCar INTEGER,
                                        LastUpdated DATETIME,
                                        HasCar BOOL,
                                        HumanVerified BOOL,
                                        Device
                                    ); """

    # Create a database connection
    rosbag_conn = create_connection(rosbag_database)

    # Create rosbag tables
    if rosbag_conn is not None:
        create_table(rosbag_conn, sql_create_rosbag_metadata_table)
        print("Successfully Created Database!")
    else:
        print("Error! Cannot create the database connection.")

    image_conn = create_connection(image_database)

    # Create image tables
    if image_conn is not None:
        create_table(image_conn, sql_create_image_metadata_table)
        print("Successfully Created Database!")
    else:
        print("Error! Cannot create the database connection.")

if __name__ == '__main__':
    main()
