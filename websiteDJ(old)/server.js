// ===================================
// WeSellYourData Biometric Server
// Node.js/Express Backend
// ===================================

const express = require('express');
const cors = require('cors');
const path = require('path');

const app = express();
const PORT = process.env.PORT || 3000;

// Middleware
app.use(cors());
app.use(express.json());
app.use(express.static('public')); // Serve static files from 'public' folder

// ===================================
// In-Memory Data Store
// ===================================
let latestData = [];
const MAX_HISTORY = 100; // Keep last 100 entries

// ===================================
// API Endpoints
// ===================================

/**
 * POST /fingerprint-data
 * Receives fingerprint data from Raspberry Pi
 * Expected format: { name: "Alice", action: "in"|"out", timestamp: 1710000000 }
 */
app.post('/fingerprint-data', (req, res) => {
    try {
        const data = req.body;
        
        // Validate incoming data
        if (!data.name || !data.action || !data.timestamp) {
            return res.status(400).json({ 
                error: 'Invalid data format. Required: name, action, timestamp' 
            });
        }
        
        if (!['in', 'out'].includes(data.action)) {
            return res.status(400).json({ 
                error: 'Invalid action. Must be "in" or "out"' 
            });
        }
        
        // Normalize timestamp (convert to milliseconds if needed)
        let timestamp = data.timestamp;
        if (typeof timestamp === 'number' && timestamp < 10000000000) {
            // Likely in seconds, convert to milliseconds
            timestamp = timestamp * 1000;
        } else if (typeof timestamp === 'string') {
            // ISO string
            timestamp = new Date(timestamp).getTime();
        }
        
        // Create standardized entry
        const entry = {
            name: data.name,
            action: data.action,
            timestamp: timestamp,
            receivedAt: Date.now()
        };
        
        // Add to data store
        latestData.unshift(entry); // Add to beginning
        
        // Trim to max history
        if (latestData.length > MAX_HISTORY) {
            latestData = latestData.slice(0, MAX_HISTORY);
        }
        
        console.log(`[${new Date().toISOString()}] New entry: ${entry.name} - ${entry.action}`);
        
        res.status(200).json({ 
            success: true, 
            message: 'Data received successfully',
            entry: entry
        });
        
    } catch (error) {
        console.error('Error processing fingerprint data:', error);
        res.status(500).json({ 
            error: 'Internal server error',
            message: error.message 
        });
    }
});

/**
 * GET /api/data
 * Retrieves all fingerprint data for the frontend
 */
app.get('/api/data', (req, res) => {
    try {
        res.json({
            success: true,
            count: latestData.length,
            data: latestData
        });
    } catch (error) {
        console.error('Error retrieving data:', error);
        res.status(500).json({ 
            error: 'Internal server error',
            message: error.message 
        });
    }
});

/**
 * GET /api/data/latest
 * Retrieves only the most recent entry
 */
app.get('/api/data/latest', (req, res) => {
    try {
        res.json({
            success: true,
            data: latestData[0] || null
        });
    } catch (error) {
        console.error('Error retrieving latest data:', error);
        res.status(500).json({ 
            error: 'Internal server error',
            message: error.message 
        });
    }
});

/**
 * DELETE /api/data
 * Clears all data (for testing/reset purposes)
 */
app.delete('/api/data', (req, res) => {
    try {
        const previousCount = latestData.length;
        latestData = [];
        
        res.json({
            success: true,
            message: `Cleared ${previousCount} entries`
        });
    } catch (error) {
        console.error('Error clearing data:', error);
        res.status(500).json({ 
            error: 'Internal server error',
            message: error.message 
        });
    }
});

/**
 * GET /api/stats
 * Get statistics about the data
 */
app.get('/api/stats', (req, res) => {
    try {
        const now = new Date();
        const todayStart = new Date(now.getFullYear(), now.getMonth(), now.getDate()).getTime();
        
        const todayEntries = latestData.filter(entry => entry.timestamp >= todayStart);
        const signInsToday = todayEntries.filter(entry => entry.action === 'in').length;
        const signOutsToday = todayEntries.filter(entry => entry.action === 'out').length;
        
        res.json({
            success: true,
            stats: {
                totalEntries: latestData.length,
                signInsToday: signInsToday,
                signOutsToday: signOutsToday,
                entriesLast24h: latestData.filter(entry => 
                    entry.timestamp >= (Date.now() - 24 * 60 * 60 * 1000)
                ).length
            }
        });
    } catch (error) {
        console.error('Error retrieving stats:', error);
        res.status(500).json({ 
            error: 'Internal server error',
            message: error.message 
        });
    }
});

// ===================================
// Health Check
// ===================================
app.get('/health', (req, res) => {
    res.json({ 
        status: 'healthy',
        timestamp: new Date().toISOString(),
        uptime: process.uptime(),
        entriesStored: latestData.length
    });
});

// ===================================
// Serve Frontend
// ===================================
app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

// ===================================
// Start Server
// ===================================
app.listen(PORT, () => {
    console.log('===========================================');
    console.log('  WeSellYourData Biometric System Server  ');
    console.log('===========================================');
    console.log(`Server running on port ${PORT}`);
    console.log(`Frontend: http://localhost:${PORT}`);
    console.log(`API Endpoint: http://localhost:${PORT}/fingerprint-data`);
    console.log(`API Docs:`);
    console.log(`  POST   /fingerprint-data  - Receive data from Raspberry Pi`);
    console.log(`  GET    /api/data          - Get all entries`);
    console.log(`  GET    /api/data/latest   - Get latest entry`);
    console.log(`  GET    /api/stats         - Get statistics`);
    console.log(`  DELETE /api/data          - Clear all data`);
    console.log(`  GET    /health            - Health check`);
    console.log('===========================================');
});
