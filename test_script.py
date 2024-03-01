import subprocess

# Command to call the object detection script with the image path
command = ['python3', 'yolov7/detect.py', '--weights', 'yolov7/runs/best.pt', '--source', "Image_0000001041_41593_471071700.jpg", "--nosave"]
# Execute the command as a subprocess
result = subprocess.run(command)

# Check if the output contains "CAR DETECTED"
print("returncode:" + str(result.returncode))
print(result.stdout)
if result.returncode == 0:
    print("Car detected!")

else:
    print("No car detected.")
