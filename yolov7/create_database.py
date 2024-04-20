import sqlite3
from sqlite3 import Error
from dotenv import load_dotenv
import os
from db_utils import load_env_variables

def create_connection(db_file):
    """ create a database connection to a SQLite database """
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        #cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        #tables = cursor.fetchall()
        #table_name = tables[0][0]
        
        print(sqlite3.version)
    except Error as e:
        print(e)
    finally:
        if conn:
            return conn #, table_name

def create_table(conn, create_table_sql):
    """ create a table from the create_table_sql statement """
    try:
        c = conn.cursor()
        c.execute(create_table_sql)
         # Commit the changes to Disk, you can execute many inserts before doing so for better runtime
        conn.commit()
    except Error as e:
        print(e)

def insert_entry(conn, entry, table_name):
    # Create a cursor object using the connection
    cursor = conn.cursor()

    # SQL statement for inserting data
    insert_sql = f"""
    INSERT INTO {table_name} (ROSBAG_UUID, RosbagFolderPath, TotalLength, PercentageCarImages, TotalImages, TotalCarImages, RacingTrackName, IsBroken, LastUpdated, Missing, LastUpdatedBeforeMissing)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
    """
    # Execute the SQL statement to insert data
    cursor.execute(insert_sql, entry)

    # Commit the changes
    conn.commit()

def update_entry(conn, entry, table_name):
    # Create a cursor object using the connection
    cursor = conn.cursor()

    # SQL statement for updating data
    update_sql = f"""
    UPDATE {table_name}
    SET RosbagFolderPath = ?, TotalLength = ?, PercentageCarImages = ?, TotalImages = ?, TotalCarImages = ?, RacingTrackName = ?, IsBroken = ?, LastUpdated = ?, Missing = ?, LastUpdatedBeforeMissing = ?
    WHERE ROSBAG_UUID = ?;
    """
    # Execute the SQL statement to update data
    cursor.execute(update_sql, (*entry[1:], entry[0]))

    # Commit the changes
    conn.commit()

def insert_or_update_entry(conn, entry, table_name):
    # Create a cursor object using the connection
    cursor = conn.cursor()

    # Check if the entry already exists in the table
    cursor.execute(f"SELECT COUNT(*) FROM {table_name} WHERE ROSBAG_UUID = ?", (entry[0],))
    count = cursor.fetchone()[0]

    if count > 0:  # Entry already exists, perform an update
        update_entry(conn, entry, table_name)
    else:  # Entry does not exist, perform an insert
        insert_entry(conn, entry, table_name)

def connect_rosbagdb():
    rosbag_database = os.path.join(root_folder, env_vars["ROSBAG_DATABASE_PATH"])
    # Create a database connection
    rosbag_conn = create_connection(rosbag_database)
    return rosbag_conn


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

    sql_create_rosbag_metadata_table = """
    CREATE TABLE IF NOT EXISTS rosbag_info (
        ROSBAG_UUID TEXT PRIMARY KEY,
        RosbagFolderPath TEXT NOT NULL,
        TotalLength INTEGER NOT NULL,
        PercentageCarImages REAL,
        TotalImages INTEGER,
        TotalCarImages INTEGER,
        RacingTrackName TEXT,
        IsBroken BOOL NOT NULL,
        LastUpdated DATESTAMP NOT NULL,
        Missing BOOL NOT NULL,
        LastUpdatedBeforeMissing DATESTAMP
    );
    """
    
    sql_create_image_metadata_table = """ CREATE TABLE IF NOT EXISTS ImageMetadata (
                                        ImageUniqueID INTEGER PRIMARY KEY,
                                        ROSBAG_UUID TEXT,
                                        XPosOfCar INTEGER,
                                        YPosOfCar INTEGER,
                                        TotalImages INTEGER,
                                        TotalCarImages INTEGER,
                                        WidthOfCar INTEGER,
                                        HeightOfCar INTEGER,
                                        CameraPosition TEXT CHECK(CameraPosition IN ('FLC', 'FRC', 'FL', 'FR', 'RR', 'RL', 'R')),
                                        CameraType TEXT CHECK(CameraType IN ('NARROW', 'WIDE')),
                                        LastUpdated DATETIME,
                                        HasCar BOOL,
                                        HumanVerified BOOL,
                                        Device,
                                        FOREIGN KEY (ROSBAG_UUID) REFERENCES RosbagMetadata(ROSBAG_UUID)
                                    ); """
    
    sql_add_foreign_key_constraint = """ALTER TABLE ImageMetadata
                                    ADD FOREIGN KEY (ROSBAG_UUID) REFERENCES RosbagMetadata(ROSBAG_UUID);"""


    # Create a database connection
    rosbag_conn = create_connection(rosbag_database)

    # Create rosbag tables
    if rosbag_conn is not None:
        create_table(rosbag_conn, sql_create_rosbag_metadata_table)
        new_entry = ("test", "test", 1, 10000, 100, 100, 'Track XYZ', False, '2024-04-03', False, None)
        #print(rosbag_table)
        insert_or_update_entry(rosbag_conn, new_entry, "rosbag_info")
        rosbag_conn.close()
        #print(f"Inserted 1 database entry into {rosbag_table}")
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
