import paho.mqtt.client as mqtt
import json, ssl, yaml, time

# 1. Load your existing config.yaml
with open('config.yaml') as f:
    config = yaml.safe_load(f)

# 2. Setup MQTT Client
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)

# 3. Callback when connected
def on_connect(client, userdata, flags, rc, *args):
    print("✓ Connected to AWS IoT Core with result code:", rc)
    # Subscribe to the same topics your Raspberry Pi subscribes to
    client.subscribe(f"{config.get('topic', 'fingerprint')}/set/#")
    print(f"✓ Subscribed to: {config.get('topic', 'fingerprint')}/set/#")
    print("\nWaiting for enrollment messages from the website...")
    print("Go to your website and click 'Start Enrollment'!\n")

# 4. Callback when message received
def on_message(client, userdata, msg, *args):
    topic = msg.topic
    payload = msg.payload.decode("utf-8")
    
    print("="*60)
    print("📩 ENROLLMENT MESSAGE RECEIVED!")
    print("="*60)
    print(f"Topic: {topic}")
    print(f"Payload: {payload}")
    
    # Try to parse as JSON
    try:
        data = json.loads(payload)
        print(f"\nParsed Data:")
        print(f"  User ID: {data.get('user_id')}")
        print(f"  User Name: {data.get('user_name')}")
    except:
        print(f"  Raw payload: {payload}")
    
    print("="*60 + "\n")
    print("✓ Website enrollment is working!")
    print("On real hardware, the Pi would now prompt: 'Place finger on sensor...'\n")

# Set callbacks
client.on_connect = on_connect
client.on_message = on_message

# TLS settings
client.tls_set(
    config['mqtt']['ca_cert'], 
    certfile=config['mqtt']['cert_file'], 
    keyfile=config['mqtt']['key_file'], 
    cert_reqs=ssl.CERT_REQUIRED, 
    tls_version=ssl.PROTOCOL_TLSv1_2
)

print("Connecting to AWS IoT Core...")
client.connect(config['mqtt']['host'], config['mqtt']['port'], 60)

print("Listener started! Press Ctrl+C to stop.\n")
client.loop_forever()