import { Platform } from 'react-native';
import Constants from 'expo-constants';

const isDevelopment = __DEV__;

const getApiBaseUrl = () => {
  if (!isDevelopment) {
    return 'https://your-production-server.com/api/v1';
  }

  const debuggerHost = Constants.expoConfig?.hostUri;
  const host = debuggerHost ? debuggerHost.split(':')[0] : 'localhost';

  console.log('🔍 Expo hostUri:', debuggerHost);
  console.log('🔍 Detected host:', host);

  if (Platform.OS === 'android' && host === 'localhost') {
    const url = 'http://10.0.2.2:8000/api/v1';
    console.log('🌐 API URL (Android emulator):', url);
    return url;
  }

  const url = `http://${host}:8000/api/v1`;
  console.log('🌐 API URL:', url);
  return url;
};

export const Config = {
  API_BASE_URL: getApiBaseUrl(),

  DRIVER_ID: null as string | null,
  get DEFAULT_DRIVER_ID(): string {
    if (!this.DRIVER_ID) {
      throw new Error("Driver ID not initialized");
    }
    return this.DRIVER_ID;
  }, // In a real app, this would come from authentication
  
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