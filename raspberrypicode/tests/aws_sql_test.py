import paho.mqtt.client as mqtt
import ssl
import json
import time

# --- YOUR SETTINGS ---
ENDPOINT = "a313wbw2spjzzg-ats.iot.us-east-1.amazonaws.com"
CA_PATH = "cert/AmazonRootCA1.pem"
CERT_PATH = "cert/2fee281c79eca72e337de63a18d668fe96214d140ca5a7df9cc4dad630ffbcc0-certificate.pem.crt"
KEY_PATH = "cert/2fee281c79eca72e337de63a18d668fe96214d140ca5a7df9cc4dad630ffbcc0-private.pem.key"
TOPIC = "fingerprint/finger"

client = mqtt.Client()

# This part tells AWS "Here are my keys"
client.tls_set(CA_PATH, certfile=CERT_PATH, keyfile=KEY_PATH, 
               cert_reqs=ssl.CERT_REQUIRED, tls_version=ssl.PROTOCOL_TLSv1_2)

print("Connecting to AWS...")
client.connect(ENDPOINT, 8883, 60) # Note the port 8883 for certificates

# Pretend finger #99 scanned
test_data = {
    "id": 99,
    "name": "TestUser",
    "action": "unlock",
    "count": 1,
    "confidence": 200
}

print(f"Sending fake finger scan to {TOPIC}...")
client.publish(TOPIC, json.dumps(test_data))

print("Done! Check your DynamoDB table now.")
time.sleep(2) # Give it a second to send before closing
client.disconnect()