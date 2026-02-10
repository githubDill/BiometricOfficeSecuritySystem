import requests
import time

# Replace this with your actual AWS API Gateway or EC2 URL
AWS_ENDPOINT = "http://3.88.243.102:3000/fingerprint-data"

def send_fingerprint_data(name, action):
    payload = {
        "name": name,
        "action": action,
        "timestamp": int(time.time())
    }
    
    try:
        # We use POST to 'push' data out to AWS
        response = requests.post(AWS_ENDPOINT, json=payload)
        
        if response.status_code == 200:
            print("Data successfully sent to AWS!")
        else:
            print(f"Failed to send. Status: {response.status_code}")
            
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    # Example: Sending a test event
    send_fingerprint_data("Eliott", "in")
    time.sleep(1)
    send_fingerprint_data("Diddy", "in")
    time.sleep(1)
    send_fingerprint_data("Trump", "in")
    time.sleep(1)
    send_fingerprint_data("Trump", "out")