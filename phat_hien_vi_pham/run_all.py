import subprocess
import time
import sys

print("Starting Traffic System...")

# chạy Flask API duy nhất
api_process = subprocess.Popen(
    [sys.executable, "app.py"]
)

time.sleep(2)

print("System is running!")
print("http://127.0.0.1:5000")

try:

    while True:
        time.sleep(1)

except KeyboardInterrupt:

    print("\nStopping system...")

    api_process.terminate()

    api_process.wait()

    print("Stopped.")