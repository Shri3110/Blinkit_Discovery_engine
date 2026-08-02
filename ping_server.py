import os
import time
import requests
import schedule

# Replace this with your actual Render deployment URL if not setting via environment variables
# Example: "https://blinkit-discovery-api.onrender.com/api/stats"
BACKEND_URL = os.getenv("BACKEND_URL", "https://blinkit-discovery-api.onrender.com/api/stats")

def ping_server():
    current_time = time.strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{current_time}] Pinging backend to prevent cold start: {BACKEND_URL}")
    try:
        # A simple GET request to a lightweight endpoint like /api/stats
        response = requests.get(BACKEND_URL, timeout=15)
        if response.status_code == 200:
            print(f"[{current_time}] Ping successful! Status: {response.status_code}")
        else:
            print(f"[{current_time}] Ping received non-200 status: {response.status_code}")
    except Exception as e:
        print(f"[{current_time}] Ping failed: {e}")

if __name__ == "__main__":
    print(f"Starting ping script. Target URL: {BACKEND_URL}")
    print("This script will ping the server every 10 minutes to prevent Render cold starts.\n")
    
    # Run once immediately on startup
    ping_server()
    
    # Schedule to run every 10 minutes
    schedule.every(10).minutes.do(ping_server)
    
    # Keep the script running
    while True:
        schedule.run_pending()
        time.sleep(60)
