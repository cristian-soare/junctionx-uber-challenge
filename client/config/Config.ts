// Environment configuration
const isDevelopment = __DEV__;

export const Config = {
  API_BASE_URL: isDevelopment 
    ? 'http://145.94.254.100:8000/api/v1'  // Your computer's IP address
    // ? 'http://10.0.2.2:8000/api/v1'     // Android emulator alternative
    // ? 'http://localhost:8000/api/v1'     // iOS simulator alternative
    : 'https://your-production-server.com/api/v1', // Production server
  
  DEFAULT_DRIVER_ID: 'driver_123', // In a real app, this would come from authentication
  
  // Timeouts
  REQUEST_TIMEOUT: 10000, // 10 seconds
  
  // Wellness settings
  BREAK_THRESHOLD_HOURS: 4.5,
  TIMER_START_SECONDS: 16190, // For demo purposes - close to break threshold
  
  // AI settings
  MAX_CHAT_HISTORY: 10,
  MAX_SUGGESTIONS: 3,
};

export default Config;