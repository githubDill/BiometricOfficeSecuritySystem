import paho.mqtt.client as mqtt
import json, ssl, yaml, time

# 1. Load your existing config.yaml
with open('config.yaml') as f:
    config = yaml.safe_load(f)

# 2. Setup MQTT Client
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.tls_set(
    config['mqtt']['ca_cert'], 
    certfile=config['mqtt']['cert_file'], 
    keyfile=config['mqtt']['key_file'], 
    cert_reqs=ssl.CERT_REQUIRED, 
    tls_version=ssl.PROTOCOL_TLSv1_2
)

# 3. Connection and Publish logic
def send_test_scan(user_id, name):
    payload = {
        "id": user_id,
        "name": name
    }
    # Match the topic from your run.py
    topic = "fingerprint/finger"
    client.publish(topic, json.dumps(payload))
    print(f"--- Sent scan for {name} (ID: {user_id}) to topic: {topic} ---")

client.connect(config['mqtt']['host'], config['mqtt']['port'], 60)
client.loop_start()

# --- THE ACTUAL TEST SEQUENCE ---
try:
    print("TEST 1: Alice enters building...")
    send_test_scan(1, "Alice")
    time.sleep(3) # Wait for AWS Lambda to process

    print("TEST 2: Bob enters building...")
    send_test_scan(2, "Bob")
    time.sleep(3)

    print("TEST 3: Alice leaves building (Scanning again toggles her out)...")
    send_test_scan(1, "Alice")
    time.sleep(3)

    print("TEST 4: Unauthorized person attempts access...")
    send_test_scan(-1, "Unknown person")
    time.sleep(3)

finally:
    client.loop_stop()
    client.disconnect()
    print("Test complete. Check your website and DynamoDB tables!")