// ===================================
// Configuration & State Management
// ===================================
const CONFIG = {
    refreshInterval: 3,
    isMonitoring: false,
    serverURL: window.location.origin // Use the same server
};

const STATE = {
    activeSessions: new Map(),
    activityHistory: [],
    statistics: {
        totalEntries: 0,
        signInsToday: 0,
        signOutsToday: 0
    },
    lastUpdate: null,
    updateInterval: null
};

// ===================================
// DOM Elements
// ===================================
const DOM = {
    // Configuration inputs
    refreshInterval: document.getElementById('refresh-interval'),
    endpointURL: document.getElementById('endpoint-url'),
    
    // Buttons
    saveConfigBtn: document.getElementById('save-config'),
    startMonitoringBtn: document.getElementById('start-monitoring'),
    refreshBtn: document.getElementById('refresh-btn'),
    clearActivityBtn: document.getElementById('clear-activity'),
    
    // Status elements
    connectionBadge: document.getElementById('connection-badge'),
    monitorText: document.getElementById('monitor-text'),
    
    // Display containers
    activeSessions: document.getElementById('active-sessions'),
    activityFeed: document.getElementById('activity-feed'),
    
    // Statistics
    activeCount: document.getElementById('active-count'),
    totalEntries: document.getElementById('total-entries'),
    signIns: document.getElementById('sign-ins'),
    signOuts: document.getElementById('sign-outs'),
    systemInfo: document.getElementById('system-info'),
    
    // Toast container
    toastContainer: document.getElementById('toast-container')
};

// ===================================
// Initialization
// ===================================
function init() {
    loadConfiguration();
    attachEventListeners();
    updateUI();
    updateEndpointDisplay();
    
    // Check server connection
    testConnection();
    
    // Auto-start monitoring
    setTimeout(() => {
        startMonitoring();
    }, 500);
    
    updateSystemInfo('System initialized');
}

// ===================================
// Configuration Management
// ===================================
function loadConfiguration() {
    const saved = localStorage.getItem('WeSellYourDataConfig');
    if (saved) {
        try {
            const config = JSON.parse(saved);
            CONFIG.refreshInterval = config.refreshInterval || 3;
            
            DOM.refreshInterval.value = CONFIG.refreshInterval;
            
            updateSystemInfo('Configuration loaded');
        } catch (error) {
            console.error('Failed to load configuration:', error);
        }
    }
}

function saveConfiguration() {
    CONFIG.refreshInterval = parseInt(DOM.refreshInterval.value) || 3;
    
    try {
        localStorage.setItem('WeSellYourDataConfig', JSON.stringify(CONFIG));
        showToast('Configuration saved successfully', 'success');
        updateSystemInfo('Configuration saved');
        
        // Restart monitoring if active
        if (CONFIG.isMonitoring) {
            stopMonitoring();
            setTimeout(startMonitoring, 500);
        }
    } catch (error) {
        showToast('Failed to save configuration', 'error');
        console.error('Save error:', error);
    }
}

function updateEndpointDisplay() {
    const serverHost = window.location.host;
    const protocol = window.location.protocol;
    const endpoint = `${protocol}//${serverHost}/fingerprint-data`;
    DOM.endpointURL.textContent = endpoint;
    updateSystemInfo(`Endpoint: ${endpoint}`);
}

// ===================================
// Event Listeners
// ===================================
function attachEventListeners() {
    DOM.saveConfigBtn.addEventListener('click', saveConfiguration);
    DOM.startMonitoringBtn.addEventListener('click', toggleMonitoring);
    DOM.refreshBtn.addEventListener('click', manualRefresh);
    DOM.clearActivityBtn.addEventListener('click', clearActivity);
}

// ===================================
// Connection Management
// ===================================
async function testConnection() {
    try {
        updateSystemInfo('Testing server connection...');
        
        const response = await fetch(`${CONFIG.serverURL}/health`, {
            method: 'GET',
            headers: { 'Accept': 'application/json' }
        });
        
        if (response.ok) {
            const data = await response.json();
            updateConnectionStatus('connected');
            updateSystemInfo(`Server connected - ${data.entriesStored} entries stored`);
        } else {
            throw new Error(`HTTP ${response.status}`);
        }
    } catch (error) {
        updateConnectionStatus('error');
        showToast(`Server connection failed: ${error.message}`, 'error');
        updateSystemInfo(`Connection error: ${error.message}`);
    }
}

function updateConnectionStatus(status) {
    DOM.connectionBadge.classList.remove('connected', 'error');
    
    if (status === 'connected') {
        DOM.connectionBadge.classList.add('connected');
        DOM.connectionBadge.querySelector('.status-text').textContent = 'Connected';
    } else if (status === 'error') {
        DOM.connectionBadge.classList.add('error');
        DOM.connectionBadge.querySelector('.status-text').textContent = 'Connection Error';
    } else {
        DOM.connectionBadge.querySelector('.status-text').textContent = 'Disconnected';
    }
}

// ===================================
// Monitoring Control
// ===================================
function toggleMonitoring() {
    if (CONFIG.isMonitoring) {
        stopMonitoring();
    } else {
        startMonitoring();
    }
}

function startMonitoring() {
    CONFIG.isMonitoring = true;
    DOM.startMonitoringBtn.classList.add('active');
    DOM.monitorText.textContent = 'Stop Monitoring';
    
    // Fetch immediately
    fetchData();
    
    // Set up interval
    STATE.updateInterval = setInterval(fetchData, CONFIG.refreshInterval * 1000);
    
    showToast('Monitoring started', 'success');
    updateSystemInfo(`Monitoring active (${CONFIG.refreshInterval}s interval)`);
}

function stopMonitoring() {
    CONFIG.isMonitoring = false;
    DOM.startMonitoringBtn.classList.remove('active');
    DOM.monitorText.textContent = 'Start Monitoring';
    
    if (STATE.updateInterval) {
        clearInterval(STATE.updateInterval);
        STATE.updateInterval = null;
    }
    
    updateConnectionStatus('disconnected');
    showToast('Monitoring stopped', 'info');
    updateSystemInfo('Monitoring stopped');
}

// ===================================
// Data Fetching & Processing
// ===================================
async function fetchData() {
    try {
        // Fetch all data
        const response = await fetch(`${CONFIG.serverURL}/api/data`, {
            method: 'GET',
            headers: { 'Accept': 'application/json' }
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        
        const result = await response.json();
        
        if (result.success && result.data) {
            processDataBatch(result.data);
            updateConnectionStatus('connected');
        }
        
        // Fetch statistics
        await fetchStatistics();
        
        STATE.lastUpdate = new Date();
        
    } catch (error) {
        console.error('Error fetching data:', error);
        updateConnectionStatus('error');
        updateSystemInfo(`Fetch error: ${error.message}`);
    }
}

async function fetchStatistics() {
    try {
        const response = await fetch(`${CONFIG.serverURL}/api/stats`, {
            method: 'GET',
            headers: { 'Accept': 'application/json' }
        });
        
        if (response.ok) {
            const result = await response.json();
            if (result.success && result.stats) {
                STATE.statistics = result.stats;
                updateStatistics();
            }
        }
    } catch (error) {
        console.error('Error fetching statistics:', error);
    }
}

function processDataBatch(dataArray) {
    // Process each entry
    dataArray.forEach(entry => {
        processEntry(entry);
    });
    
    updateUI();
}

function processEntry(data) {
    // Validate data
    if (!data.name || !data.action) {
        console.warn('Invalid data entry:', data);
        return;
    }
    
    // Convert timestamp
    let timestamp = data.timestamp;
    if (typeof timestamp === 'number') {
        timestamp = new Date(timestamp);
    } else if (typeof timestamp === 'string') {
        timestamp = new Date(timestamp);
    } else {
        timestamp = new Date();
    }
    
    // Check if this entry is already in history
    const isDuplicate = STATE.activityHistory.some(entry => 
        entry.name === data.name && 
        entry.action === data.action && 
        Math.abs(entry.timestamp - timestamp) < 1000 // Within 1 second
    );
    
    if (isDuplicate) {
        return; // Skip duplicate
    }
    
    // Create standardized entry
    const entry = {
        name: data.name,
        action: data.action,
        timestamp: timestamp,
        id: `${data.name}-${data.action}-${timestamp.getTime()}`
    };
    
    // Update active sessions
    if (entry.action === 'in') {
        STATE.activeSessions.set(entry.name, {
            name: entry.name,
            startTime: entry.timestamp
        });
    } else if (entry.action === 'out') {
        STATE.activeSessions.delete(entry.name);
    }
    
    // Add to activity history (at the beginning)
    STATE.activityHistory.unshift(entry);
    
    // Limit history to 50 items
    if (STATE.activityHistory.length > 50) {
        STATE.activityHistory = STATE.activityHistory.slice(0, 50);
    }
}

// ===================================
// UI Updates
// ===================================
function updateUI() {
    updateActiveSessions();
    updateActivityFeed();
    updateActiveCount();
}

function updateActiveCount() {
    DOM.activeCount.textContent = STATE.activeSessions.size;
}

function updateActiveSessions() {
    if (STATE.activeSessions.size === 0) {
        DOM.activeSessions.innerHTML = `
            <div class="empty-state">
                <svg viewBox="0 0 100 100" width="60" height="60">
                    <circle cx="50" cy="50" r="40" fill="none" stroke="currentColor" stroke-width="2" stroke-dasharray="5,5" opacity="0.3"/>
                </svg>
                <p>No active sessions</p>
            </div>
        `;
        return;
    }
    
    const sessionsHTML = Array.from(STATE.activeSessions.values())
        .map(session => {
            const duration = formatDuration(new Date() - session.startTime);
            return `
                <div class="session-card">
                    <div class="session-info">
                        <span class="session-name">${escapeHtml(session.name)}</span>
                        <span class="session-time">${session.startTime.toLocaleTimeString()}</span>
                    </div>
                    <div class="session-status">Active • ${duration}</div>
                </div>
            `;
        })
        .join('');
    
    DOM.activeSessions.innerHTML = sessionsHTML;
}

function updateActivityFeed() {
    if (STATE.activityHistory.length === 0) {
        DOM.activityFeed.innerHTML = `
            <div class="empty-state">
                <svg viewBox="0 0 100 100" width="60" height="60">
                    <rect x="20" y="30" width="60" height="8" rx="4" fill="currentColor" opacity="0.2"/>
                    <rect x="20" y="46" width="40" height="8" rx="4" fill="currentColor" opacity="0.2"/>
                    <rect x="20" y="62" width="50" height="8" rx="4" fill="currentColor" opacity="0.2"/>
                </svg>
                <p>No recent activity</p>
            </div>
        `;
        return;
    }
    
    const activityHTML = STATE.activityHistory
        .map(entry => {
            const icon = entry.action === 'in' ? '→' : '←';
            const iconClass = entry.action === 'in' ? 'sign-in' : 'sign-out';
            const actionText = entry.action === 'in' ? 'Signed in' : 'Signed out';
            
            return `
                <div class="activity-item">
                    <div class="activity-icon ${iconClass}">${icon}</div>
                    <div class="activity-details">
                        <div class="activity-name">${escapeHtml(entry.name)}</div>
                        <div class="activity-action">${actionText}</div>
                    </div>
                    <div class="activity-timestamp">${entry.timestamp.toLocaleTimeString()}</div>
                </div>
            `;
        })
        .join('');
    
    DOM.activityFeed.innerHTML = activityHTML;
}

function updateStatistics() {
    DOM.totalEntries.textContent = STATE.statistics.totalEntries || 0;
    DOM.signIns.textContent = STATE.statistics.signInsToday || 0;
    DOM.signOuts.textContent = STATE.statistics.signOutsToday || 0;
}

// ===================================
// Control Actions
// ===================================
async function manualRefresh() {
    showToast('Refreshing data...', 'info');
    await fetchData();
    showToast('Data refreshed', 'success');
}

async function clearActivity() {
    if (!confirm('Clear all activity history? This will only clear the display, not the server data.')) {
        return;
    }
    
    STATE.activityHistory = [];
    STATE.activeSessions.clear();
    updateUI();
    showToast('Activity history cleared', 'info');
    updateSystemInfo('Activity history cleared');
}

// ===================================
// Toast Notifications
// ===================================
function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    
    const icon = type === 'success' ? '✓' : type === 'error' ? '✕' : 'ℹ';
    
    toast.innerHTML = `
        <div class="toast-icon">${icon}</div>
        <div class="toast-content">
            <div class="toast-message">${escapeHtml(message)}</div>
        </div>
        <button class="toast-close">×</button>
    `;
    
    const closeBtn = toast.querySelector('.toast-close');
    closeBtn.addEventListener('click', () => removeToast(toast));
    
    DOM.toastContainer.appendChild(toast);
    
    // Auto remove after 5 seconds
    setTimeout(() => removeToast(toast), 5000);
}

function removeToast(toast) {
    if (!toast.parentNode) return;
    
    toast.classList.add('removing');
    setTimeout(() => {
        if (toast.parentNode) {
            toast.remove();
        }
    }, 300);
}

// ===================================
// Utility Functions
// ===================================
function updateSystemInfo(message) {
    DOM.systemInfo.textContent = message;
    console.log(`[WeSellYourData] ${message}`);
}

function formatDuration(milliseconds) {
    const seconds = Math.floor(milliseconds / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);
    
    if (hours > 0) {
        return `${hours}h ${minutes % 60}m`;
    } else if (minutes > 0) {
        return `${minutes}m ${seconds % 60}s`;
    } else {
        return `${seconds}s`;
    }
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// ===================================
// CSS Animation Helper
// ===================================
const style = document.createElement('style');
style.textContent = `
    .spin {
        animation: spin 1s linear infinite;
    }
    
    @keyframes spin {
        from { transform: rotate(0deg); }
        to { transform: rotate(360deg); }
    }
`;
document.head.appendChild(style);

// ===================================
// Initialize on DOM Load
// ===================================
document.addEventListener('DOMContentLoaded', init);
