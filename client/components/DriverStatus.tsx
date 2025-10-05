import React, { useState, useEffect, useRef } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  Alert,
  Modal,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';

interface DriverStatusProps {
  navigation: any;
  driverId: string;
}

const DriverStatusComponent: React.FC<DriverStatusProps> = ({ navigation, driverId }) => {
  const [isDriving, setIsDriving] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [drivingSeconds, setDrivingSeconds] = useState(0);
  const [showWellnessModal, setShowWellnessModal] = useState(false);
  const timerRef = useRef<NodeJS.Timeout | null>(null);
  
  const serverUrl = 'http://localhost:8000/api/v1'; // Adjust based on your server config
  const BREAK_THRESHOLD_SECONDS = 16200; // 4.5 hours
  const TIMER_START_SECONDS = 16190; // Start close to threshold for demo

  useEffect(() => {
    if (isDriving && !isPaused) {
      timerRef.current = setInterval(() => {
        setDrivingSeconds(prev => {
          const newSeconds = prev + 1;
          
          // Check for wellness reminder
          if (newSeconds >= BREAK_THRESHOLD_SECONDS && prev < BREAK_THRESHOLD_SECONDS) {
            checkWellnessReminder(newSeconds / 3600); // Convert to hours
          }
          
          return newSeconds;
        });
      }, 1000);
    } else {
      if (timerRef.current) {
        clearInterval(timerRef.current);
        timerRef.current = null;
      }
    }

    return () => {
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
    };
  }, [isDriving, isPaused]);

  const checkWellnessReminder = async (hoursSpent: number) => {
    try {
      const response = await fetch(`${serverUrl}/ai/wellness/${driverId}?hours_driven=${hoursSpent}`);
      if (response.ok) {
        const data = await response.json();
        if (data.wellness_reminder) {
          setShowWellnessModal(true);
        }
      }
    } catch (error) {
      console.warn('Failed to check wellness reminder:', error);
    }
  };

  const toggleDriving = () => {
    if (isDriving) {
      // Going offline
      setDrivingSeconds(0);
      setIsPaused(false);
      setIsDriving(false);
      setShowWellnessModal(false);
    } else {
      // Going online
      setDrivingSeconds(TIMER_START_SECONDS);
      setIsDriving(true);
    }
  };

  const togglePause = () => {
    setIsPaused(!isPaused);
  };

  const formatDuration = (totalSeconds: number): string => {
    const hours = Math.floor(totalSeconds / 3600);
    const minutes = Math.floor((totalSeconds % 3600) / 60);
    const seconds = totalSeconds % 60;
    
    if (hours > 0) {
      return `${hours}h ${minutes}m`;
    }
    return `${minutes}m ${seconds}s`;
  };

  const handleWellnessChat = () => {
    setShowWellnessModal(false);
    const hoursSpent = drivingSeconds / 3600;
    const wellnessPrompt = `Hey there! You've been driving for ${hoursSpent.toFixed(1)} hours now. Time for a well-deserved break! Let me know if you'd like some ideas for how to best spend your break time.`;
    
    navigation.navigate('AIChat', {
      initialPrompt: wellnessPrompt
    });
  };

  const dismissWellnessModal = () => {
    setShowWellnessModal(false);
  };

  const getStatusColor = () => {
    if (isDriving && !isPaused) return '#34C759'; // Green
    if (isDriving && isPaused) return '#FF9500'; // Orange
    return '#8E8E93'; // Gray
  };

  const getStatusText = () => {
    if (!isDriving) return 'Offline';
    if (isPaused) return 'Paused';
    return 'Online';
  };

  return (
    <>
      <View style={styles.container}>
        <View style={styles.statusRow}>
          <View style={styles.statusIndicator}>
            <View style={[styles.statusDot, { backgroundColor: getStatusColor() }]} />
            <View style={styles.statusInfo}>
              <Text style={styles.statusText}>{getStatusText()}</Text>
              {isDriving && (
                <Text style={styles.timerText}>
                  {formatDuration(drivingSeconds)}
                </Text>
              )}
            </View>
          </View>

          <View style={styles.controls}>
            {isDriving && (
              <TouchableOpacity
                style={[styles.controlButton, styles.pauseButton]}
                onPress={togglePause}
              >
                <Ionicons 
                  name={isPaused ? "play" : "pause"} 
                  size={16} 
                  color="white" 
                />
                <Text style={styles.controlButtonText}>
                  {isPaused ? "Resume" : "Pause"}
                </Text>
              </TouchableOpacity>
            )}

            <TouchableOpacity
              style={[
                styles.controlButton,
                styles.powerButton,
                { backgroundColor: isDriving ? '#FF3B30' : '#34C759' }
              ]}
              onPress={toggleDriving}
            >
              <Ionicons name="power" size={16} color="white" />
              <Text style={styles.controlButtonText}>
                {isDriving ? "Go Offline" : "Go Online"}
              </Text>
            </TouchableOpacity>
          </View>
        </View>
      </View>

      {/* Wellness Modal */}
      <Modal
        visible={showWellnessModal}
        transparent={true}
        animationType="slide"
        onRequestClose={dismissWellnessModal}
      >
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <View style={styles.modalHeader}>
              <Ionicons name="cafe" size={32} color="#FF9500" />
              <Text style={styles.modalTitle}>Time for a break?</Text>
            </View>
            
            <Text style={styles.modalText}>
              You've been driving for {(drivingSeconds / 3600).toFixed(1)} hours. 
              A 15-30 minute break can help you recharge and stay safe.
            </Text>

            <View style={styles.modalButtons}>
              <TouchableOpacity
                style={[styles.modalButton, styles.chatButton]}
                onPress={handleWellnessChat}
              >
                <Text style={styles.chatButtonText}>Get Break Ideas</Text>
              </TouchableOpacity>
              
              <TouchableOpacity
                style={[styles.modalButton, styles.dismissButton]}
                onPress={dismissWellnessModal}
              >
                <Text style={styles.dismissButtonText}>Dismiss</Text>
              </TouchableOpacity>
            </View>
          </View>
        </View>
      </Modal>
    </>
  );
};

const styles = StyleSheet.create({
  container: {
    backgroundColor: 'white',
    borderRadius: 12,
    padding: 16,
    marginHorizontal: 16,
    marginVertical: 8,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  statusRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  statusIndicator: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
  },
  statusDot: {
    width: 12,
    height: 12,
    borderRadius: 6,
    marginRight: 12,
  },
  statusInfo: {
    flex: 1,
  },
  statusText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#333',
  },
  timerText: {
    fontSize: 14,
    color: '#666',
    marginTop: 2,
  },
  controls: {
    flexDirection: 'row',
    gap: 8,
  },
  controlButton: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 8,
    gap: 4,
  },
  powerButton: {
    // backgroundColor set dynamically
  },
  pauseButton: {
    backgroundColor: '#FF9500',
  },
  controlButtonText: {
    color: 'white',
    fontSize: 12,
    fontWeight: '600',
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    justifyContent: 'flex-end',
  },
  modalContent: {
    backgroundColor: 'white',
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    padding: 24,
    paddingBottom: 40,
  },
  modalHeader: {
    alignItems: 'center',
    marginBottom: 16,
  },
  modalTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#333',
    marginTop: 8,
  },
  modalText: {
    fontSize: 16,
    color: '#666',
    textAlign: 'center',
    lineHeight: 22,
    marginBottom: 24,
  },
  modalButtons: {
    flexDirection: 'row',
    gap: 12,
  },
  modalButton: {
    flex: 1,
    paddingVertical: 14,
    borderRadius: 8,
    alignItems: 'center',
  },
  chatButton: {
    backgroundColor: '#007AFF',
  },
  dismissButton: {
    backgroundColor: '#F2F2F7',
  },
  chatButtonText: {
    color: 'white',
    fontSize: 16,
    fontWeight: '600',
  },
  dismissButtonText: {
    color: '#333',
    fontSize: 16,
    fontWeight: '600',
  },
});

export default DriverStatusComponent;