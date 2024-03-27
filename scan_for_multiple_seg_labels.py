import os

def find_files_with_more_than_two_lines(path):
    """
    Finds and returns a list of filenames in the given path where each file contains
    more than two lines of text, excluding empty lines.

    Parameters:
    - path: The directory path to search for .txt files.

    Returns:
    - A list of filenames (not full paths) of files having more than two non-empty lines.
    """
    filenames_with_more_than_two_lines = []  # Initialize an empty list to store results

    # Loop through all files in the given directory
    for filename in os.listdir(path):
        # Check if the file is a .txt file
        if filename.endswith(".txt"):
            file_path = os.path.join(path, filename)  # Construct full file path

            # Open and read the file
            with open(file_path, 'r', encoding='utf-8') as file:
                lines = file.readlines()  # Read all lines in the file
                
                # Filter out empty lines (stripped of whitespace)
                non_empty_lines = [line for line in lines if line.strip()]
                
                # Check if there are more than two non-empty lines
                if len(non_empty_lines) > 2:
                    filenames_with_more_than_two_lines.append(filename)

    return filenames_with_more_than_two_lines

def move_directories_with_multiple_segments(root_path):
    """
    Moves directories with multiple segment files, as well as their corresponding
    directories, into a 'multiple_segments' directory within the root_path.

    Parameters:
    - root_path: The root directory path to start searching from.
    """
    all_files = find_files_with_more_than_two_lines(root_path)
    target_path = os.path.join(root_path, 'multiple_segments')

    # Ensure the target directory exists
    if not os.path.exists(target_path):
        os.makedirs(target_path)

    for labels_path in all_files.keys():
        # Strip '/train/labels/' from the path to get the base directory for segments
        base_segment_path = labels_path.rsplit('/train/labels', 1)[0]

        # Identify the corresponding directory by removing the '_converted_to_segments' suffix
        corresponding_dir_path = base_segment_path.rsplit('_converted_to_segments', 1)[0]

        # Define new paths in the target directory
        new_base_segment_path = os.path.join(target_path, os.path.basename(base_segment_path))
        new_corresponding_dir_path = os.path.join(target_path, os.path.basename(corresponding_dir_path))

        # Move the directories if they exist and not already in the target location
        if os.path.exists(base_segment_path) and base_segment_path != new_base_segment_path:
            shutil.move(base_segment_path, new_base_segment_path)
            print(f"Moved {base_segment_path} to {new_base_segment_path}")

        if os.path.exists(corresponding_dir_path) and corresponding_dir_path != new_corresponding_dir_path:
            shutil.move(corresponding_dir_path, new_corresponding_dir_path)
            print(f"Moved {corresponding_dir_path} to {new_corresponding_dir_path}")


# Example usage
path = '/home/chris-lai/yolov8/converted_data/'  # Replace with your actual directory path
files = move_directories_with_multiple_segments(path)

# print("Files with more than two lines of text:")
# for f in files:
#     print(f)