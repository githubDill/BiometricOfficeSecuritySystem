# WeSellYourData Biometric Office System

A professional biometric fingerprint office management system with a Node.js backend and beautiful web frontend.

## Overview

This system consists of:
- **Backend Server** (Node.js/Express) - Receives fingerprint data from Raspberry Pi and serves the frontend
- **Frontend Dashboard** - Real-time monitoring interface for office sign-ins/sign-outs
- **API Endpoints** - RESTful API for data management

## Architecture

```
Raspberry Pi (Fingerprint Scanner)
        |
        | POST /fingerprint-data
        |
        ▼
Your AWS Server (Node.js)
        |
        | Stores data in memory
        | Serves frontend
        |
        ▼
Browser Dashboard
```

## Installation

### Prerequisites

- Node.js 14+ and npm
- AWS EC2 instance (or any server) with Elastic IP
- Raspberry Pi with fingerprint scanner

### Step 1: Install Dependencies

```bash
npm install
```

This will install:
- `express` - Web server framework
- `cors` - Cross-origin resource sharing
- `nodemon` - Development auto-reload (optional)

### Step 2: Configure Your Server

1. **For Development:**
```bash
npm run dev
# Server runs on http://localhost:3000
```

2. **For Production:**
```bash
npm start
# Server runs on port 3000 (or PORT environment variable)
```

3. **On AWS EC2:**
```bash
# Set environment variable for production port
export PORT=80  # or 443 for HTTPS

# Run with PM2 for process management
npm install -g pm2
pm2 start server.js --name biometric-system
pm2 save
pm2 startup
```

### Step 3: Configure Firewall

Open the necessary ports on your AWS Security Group:
- Port 3000 (or your chosen port) - HTTP access
- Port 80 - Standard HTTP (if using)
- Port 443 - HTTPS (if using SSL)

## Raspberry Pi Configuration

Configure your Raspberry Pi to send fingerprint data to your server:

### Endpoint URL
```
http://YOUR_ELASTIC_IP:3000/fingerprint-data
```

### Data Format (POST request)
```json
{
  "name": "Alice Johnson",
  "action": "in",
  "timestamp": 1710000000
}
```

### Field Requirements:
- `name` (string, required) - User's name
- `action` (string, required) - Must be "in" or "out"
- `timestamp` (number or ISO string, required) - Unix timestamp in seconds/milliseconds or ISO date string

### Example Python Code for Raspberry Pi
```python
import requests
import time

SERVER_URL = "http://YOUR_ELASTIC_IP:3000/fingerprint-data"

def send_fingerprint_data(name, action):
    data = {
        "name": name,
        "action": action,
        "timestamp": int(time.time())
    }
    
    try:
        response = requests.post(SERVER_URL, json=data)
        if response.status_code == 200:
            print(f"✓ Data sent: {name} - {action}")
        else:
            print(f"✗ Error: {response.status_code}")
    except Exception as e:
        print(f"✗ Connection error: {e}")

# Example usage
send_fingerprint_data("Alice Johnson", "in")
```

## API Documentation

### POST /fingerprint-data
Receives fingerprint scan data from Raspberry Pi

**Request:**
```json
{
  "name": "Alice Johnson",
  "action": "in",
  "timestamp": 1710000000
}
```

**Response:**
```json
{
  "success": true,
  "message": "Data received successfully",
  "entry": {
    "name": "Alice Johnson",
    "action": "in",
    "timestamp": 1710000000000,
    "receivedAt": 1710000001234
  }
}
```

### GET /api/data
Retrieves all stored fingerprint entries

**Response:**
```json
{
  "success": true,
  "count": 25,
  "data": [
    {
      "name": "Alice Johnson",
      "action": "in",
      "timestamp": 1710000000000,
      "receivedAt": 1710000001234
    }
  ]
}
```

### GET /api/stats
Get system statistics

**Response:**
```json
{
  "success": true,
  "stats": {
    "totalEntries": 100,
    "signInsToday": 15,
    "signOutsToday": 12,
    "entriesLast24h": 27
  }
}
```

### GET /health
Server health check

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-03-01T12:00:00.000Z",
  "uptime": 3600.5,
  "entriesStored": 100
}
```

### DELETE /api/data
Clear all stored data (use with caution)

**Response:**
```json
{
  "success": true,
  "message": "Cleared 100 entries"
}
```

## Frontend Usage

Once the server is running, access the dashboard at:
```
http://YOUR_ELASTIC_IP:3000
```

### Features:
- **Real-time Monitoring** - Auto-refreshes every 3 seconds (configurable)
- **Active Sessions** - Shows currently signed-in users
- **Activity Feed** - Recent sign-in/sign-out history
- **Statistics** - Total entries, daily sign-ins, daily sign-outs
- **Configuration** - Adjust refresh interval

## Deployment Tips

### Using HTTPS (Recommended for Production)

1. **Install Certbot (Let's Encrypt):**
```bash
sudo apt-get install certbot
sudo certbot certonly --standalone -d your-domain.com
```

2. **Update server.js for HTTPS:**
```javascript
const https = require('https');
const fs = require('fs');

const options = {
  key: fs.readFileSync('/etc/letsencrypt/live/your-domain.com/privkey.pem'),
  cert: fs.readFileSync('/etc/letsencrypt/live/your-domain.com/fullchain.pem')
};

https.createServer(options, app).listen(443, () => {
  console.log('HTTPS Server running on port 443');
});
```

## File Structure

```
biometric-system/
├── server.js           # Backend server
├── package.json        # Dependencies
├── public/             # Frontend files
│   ├── index.html      # Dashboard HTML
│   ├── style.css       # Styles
│   └── script.js       # Frontend JavaScript
└── README.md          # This file
```

## Troubleshooting

### Server won't start
```bash
# Check if port is already in use
sudo lsof -i :3000

# Kill process using the port
sudo kill -9 <PID>
```

### Raspberry Pi can't connect
- Verify server IP address and port
- Check AWS Security Group allows incoming traffic
- Test with curl: `curl -X POST http://YOUR_IP:3000/health`

### Frontend shows "Connection Error"
- Ensure server is running
- Check browser console for errors
- Verify API endpoints are accessible
