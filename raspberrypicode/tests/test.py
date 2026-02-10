import paho.mqtt.client as mqtt
import ssl
import time
import json

# --- SETTINGS ---
ENDPOINT = "a313wbw2spjzzg-ats.iot.us-east-1.amazonaws.com"
CA_PATH = "cert/AmazonRootCA1.pem"
CERT_PATH = "cert/2fee281c79eca72e337de63a18d668fe96214d140ca5a7df9cc4dad630ffbcc0-certificate.pem.crt"
KEY_PATH = "cert/2fee281c79eca72e337de63a18d668fe96214d140ca5a7df9cc4dad630ffbcc0-private.pem.key"

TOPIC_SUB = "fingerprint/control"
TOPIC_PUB = "fingerprint/data"

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("✅ Connected to AWS!")
        client.subscribe(TOPIC_SUB)
        print(f"👂 Subscribed to: {TOPIC_SUB}")
    else:
        print(f"❌ Connection failed: {rc}")

def on_message(client, userdata, msg):
    print(f"\n📩 [RECEIVE] Topic: {msg.topic}")
    print(f"   Payload: {msg.payload.decode()}")

# Setup Client
client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

client.tls_set(CA_PATH, certfile=CERT_PATH, keyfile=KEY_PATH, 
               cert_reqs=ssl.CERT_REQUIRED, tls_version=ssl.PROTOCOL_TLSv1_2)

print("Connecting...")
client.connect(ENDPOINT, 8883, 60)

# Start background thread
client.loop_start()

try:
    print("--- Bi-directional Test Started (Ctrl+C to stop) ---")
    while True:
        # Create a test payload
        payload = {"status": "alive", "timestamp": time.ctime()}
        
        print(f"🚀 [SEND] Sending status to {TOPIC_PUB}...")
        client.publish(TOPIC_PUB, json.dumps(payload))
        
        print("😴 Waiting 10 seconds... (Try sending a message from AWS Console now!)")
        time.sleep(10)

except KeyboardInterrupt:
    print("\nStopping...")
    client.loop_stop()
    client.disconnect()