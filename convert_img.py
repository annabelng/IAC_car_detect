import cv2
import numpy as np
import argparse

def save_image_array_as_npy(image_path):
    # Read the JPG image into a NumPy array
    img = cv2.imread(image_path)

    # Check if the image was successfully loaded
    if img is None:
        print("Error: Unable to load image")
    else:
        # Save the NumPy array as a .npy file
        np.savez("test_img.npz", img)
        print("Image array saved successfully as image_array.npy")

if __name__ == "__main__":
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='Convert JPG image to NumPy array and save as .npy file')
    parser.add_argument('--image_path', type=str, help='Path to the JPG image file')
    args = parser.parse_args()

    # Call the function with the provided image path
    save_image_array_as_npy(args.image_path)