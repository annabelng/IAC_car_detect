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
    database = os.path.join(root_folder, env_vars["ROSBAG_DATABASE_PATH"])
    print("Database PATH:", database)

    sql_create_rosbag_metadata_table = """ CREATE TABLE IF NOT EXISTS RosbagMetadata (
                                        RosbagFolderPath TEXT PRIMARY KEY,
                                        TotalLength INTEGER NOT NULL,
                                        PercentageCarImages REAL NOT NULL,
                                        TotalImages INTEGER NOT NULL,
                                        TotalCarImages INTEGER NOT NULL,
                                        TrackType TEXT,
                                        IsBroken BOOL
                                    ); """

    # Create a database connection
    conn = create_connection(database)

    # Create tables
    if conn is not None:
        create_table(conn, sql_create_rosbag_metadata_table)
        print("Successfully Created Database!")
    else:
        print("Error! Cannot create the database connection.")

if __name__ == '__main__':
    main()
