import subprocess
import time
import sys

print("Starting Traffic System...")

# chạy API
api_process = subprocess.Popen([sys.executable, "-m", "api.app"])

time.sleep(2)

# chạy AI
ai_process = subprocess.Popen([sys.executable, "-m", "AI.main"])

print("System is running!")
print("Open web at: http://127.0.0.1:5500/traffic_web/index.html")

# giữ chương trình chạy
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("\nStopping system...")
    api_process.terminate()
    ai_process.terminate()
