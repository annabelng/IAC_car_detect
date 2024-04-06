import os
from dotenv import load_dotenv

# Path to the .env file (assuming it's located in the same directory as utils.py)
root_folder = os.path.join(os.path.dirname(__file__), '..')
dotenv_path = os.path.join(root_folder, '.env')

def load_env_variables():
    """
    Loads variables from the .env file and returns a dictionary.
    """
    load_dotenv(dotenv_path)
    env_variables = {}

    # Read all environment variables from .env file
    with open(dotenv_path, 'r') as file:
        for line in file:
            if line.strip() and not line.startswith('#'):
                key, value = line.strip().split('=', 1)
                env_variables[key] = value

    return env_variables