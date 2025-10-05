// Environment configuration
import { Platform } from 'react-native';

const isDevelopment = __DEV__;

// IMPORTANT: If using Expo Go or physical device with tunnel mode,
// replace with your computer's IP address (run `ipconfig getifaddr en0` on Mac)
const LOCAL_IP = '172.20.10.2'; // Your computer's IP - use 'localhost' for web/simulator only

// Get the appropriate base URL based on platform
const getApiBaseUrl = () => {
  if (!isDevelopment) {
    return 'https://your-production-server.com/api/v1';
  }

  // For development
  if (Platform.OS === 'web') {
    return `http://${LOCAL_IP}:8000/api/v1`;
  }

  // For iOS simulator, localhost usually works, but use IP if connecting from physical device
  if (Platform.OS === 'ios') {
    return `http://${LOCAL_IP}:8000/api/v1`;
  }

  // For Android emulator, use 10.0.2.2 instead of localhost (or use physical device IP)
  if (Platform.OS === 'android') {
    return `http://${LOCAL_IP}:8000/api/v1`;
  }

  // Fallback
  return `http://${LOCAL_IP}:8000/api/v1`;
};

export const Config = {
  API_BASE_URL: getApiBaseUrl(),

  DEFAULT_DRIVER_ID: 'soare', // In a real app, this would come from authentication
  
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