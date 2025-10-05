import AsyncStorage from '@react-native-async-storage/async-storage';
import Config from '../config/Config';

const DRIVER_ID_KEY = '@driver_id';

export async function getOrCreateDriverId(): Promise<string> {
  try {
    let driverId = await AsyncStorage.getItem(DRIVER_ID_KEY);

    if (!driverId) {
      driverId = generateRandomDriverId();
      await AsyncStorage.setItem(DRIVER_ID_KEY, driverId);
      await registerDriver(driverId);
    }

    return driverId;
  } catch (error) {
    console.error('Failed to get/create driver ID:', error);
    return generateRandomDriverId();
  }
}

function generateRandomDriverId(): string {
  const chars = 'abcdefghijklmnopqrstuvwxyz0123456789';
  let id = 'driver_';
  for (let i = 0; i < 8; i++) {
    id += chars.charAt(Math.floor(Math.random() * chars.length));
  }
  return id;
}

async function registerDriver(driverId: string): Promise<void> {
  try {
    const response = await fetch(`${Config.API_BASE_URL}/drivers/register`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        driver_id: driverId,
        city_id: 1,
        timestamp: new Date().toISOString(),
      }),
    });

    if (!response.ok) {
      console.error('Failed to register driver:', response.status);
    } else {
      console.log('Driver registered:', driverId);
    }
  } catch (error) {
    console.error('Failed to register driver:', error);
  }
}
