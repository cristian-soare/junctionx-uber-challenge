import Slider from "@react-native-community/slider";
import React, { useEffect, useRef, useState } from "react";
import {
  Alert,
  Animated,
  Dimensions,
  Modal,
  PanResponder,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from "react-native";
import Config from "../config/Config";
import { hourToTimeString } from "../models/api";
import { getOptimalTime, saveWorkingHours } from "../services/preferencesService";

interface SchedulePanelProps {
  visible: boolean;
  onClose: () => void;
  onSchedule: (optimalTime: string, optimalTimeHour: number, nrHours: number) => void;
}

const TIME_SLOTS = [
  "00:00",
  "01:00",
  "02:00",
  "03:00",
  "04:00",
  "05:00",
  "06:00",
  "07:00",
  "08:00",
  "09:00",
  "10:00",
  "11:00",
  "12:00",
  "13:00",
  "14:00",
  "15:00",
  "16:00",
  "17:00",
  "18:00",
  "19:00",
  "20:00",
  "21:00",
  "22:00",
  "23:00",
];

const SCREEN_HEIGHT = Dimensions.get("window").height;

export default function SchedulePanel({ visible, onClose, onSchedule }: SchedulePanelProps) {
  const [startIndex, setStartIndex] = useState<number | null>(null);
  const [endIndex, setEndIndex] = useState<number | null>(null);
  const [hours, setHours] = useState(1);
  const [isLoading, setIsLoading] = useState(false);
  const slideAnim = useRef(new Animated.Value(SCREEN_HEIGHT)).current;

  useEffect(() => {
    if (visible) {
      // Reset to bottom before animating up
      slideAnim.setValue(SCREEN_HEIGHT);
      Animated.spring(slideAnim, {
        toValue: 0,
        useNativeDriver: true,
        tension: 65,
        friction: 11,
      }).start();
    } else {
      Animated.timing(slideAnim, {
        toValue: SCREEN_HEIGHT,
        duration: 300,
        useNativeDriver: true,
      }).start();
      // Reset selections when closing
      setStartIndex(null);
      setEndIndex(null);
      setHours(1);
    }
  }, [visible]);

  const panResponder = useRef(
    PanResponder.create({
      onStartShouldSetPanResponder: () => true,
      onMoveShouldSetPanResponder: (_, gestureState) => {
        return gestureState.dy > 5;
      },
      onPanResponderMove: (_, gestureState) => {
        if (gestureState.dy > 0) {
          slideAnim.setValue(gestureState.dy);
        }
      },
      onPanResponderRelease: (_, gestureState) => {
        if (gestureState.dy > 100 || gestureState.vy > 0.5) {
          Animated.timing(slideAnim, {
            toValue: SCREEN_HEIGHT,
            duration: 300,
            useNativeDriver: true,
          }).start(() => onClose());
        } else {
          Animated.spring(slideAnim, {
            toValue: 0,
            useNativeDriver: true,
            tension: 65,
            friction: 11,
          }).start();
        }
      },
    }),
  ).current;

  const handleTimeSlotPress = (index: number) => {
    if (startIndex === null) {
      // First selection - set start
      setStartIndex(index);
      setEndIndex(null);
    } else if (endIndex === null) {
      // Second selection - set end
      if (index > startIndex) {
        setEndIndex(index);
      } else {
        // If user clicks before start, reset and set new start
        setStartIndex(index);
        setEndIndex(null);
      }
    } else {
      // Reset and start new selection
      setStartIndex(index);
      setEndIndex(null);
    }
  };

  const isInRange = (index: number) => {
    if (startIndex === null) return false;
    if (endIndex === null) return index === startIndex;
    return index >= startIndex && index <= endIndex;
  };

  const isEdge = (index: number) => {
    return index === startIndex || index === endIndex;
  };

  const calculateHours = () => {
    if (startIndex !== null && endIndex !== null) {
      return endIndex - startIndex;
    }
    return hours;
  };

  if (!visible) return null;

  return (
    <Modal visible={visible} transparent animationType="none" onRequestClose={onClose}>
      <TouchableOpacity style={styles.backdrop} activeOpacity={1} onPress={onClose}>
        <Animated.View
          style={[
            styles.container,
            {
              transform: [{ translateY: slideAnim }],
            },
          ]}
        >
          <View {...panResponder.panHandlers}>
            <View style={styles.handle}>
              <View style={styles.handleBar} />
            </View>

            <View style={styles.content}>
              <Text style={styles.title}>Schedule your drive</Text>

              <View style={styles.section}>
                <Text style={styles.label}>
                  {startIndex === null
                    ? "Select start time"
                    : endIndex === null
                      ? "Select end time"
                      : `${TIME_SLOTS[startIndex]} - ${TIME_SLOTS[endIndex]} (${calculateHours()}h)`}
                </Text>
                <View style={styles.timeGrid}>
                  {TIME_SLOTS.map((time, index) => (
                    <TouchableOpacity
                      key={`${time}-${index}`}
                      style={[
                        styles.timeSlot,
                        isInRange(index) && styles.timeSlotInRange,
                        isEdge(index) && styles.timeSlotSelected,
                      ]}
                      onPress={() => handleTimeSlotPress(index)}
                      activeOpacity={0.7}
                    >
                      <Text
                        style={[
                          styles.timeSlotText,
                          isInRange(index) && styles.timeSlotTextInRange,
                          isEdge(index) && styles.timeSlotTextSelected,
                        ]}
                      >
                        {time}
                      </Text>
                    </TouchableOpacity>
                  ))}
                </View>
              </View>

              <View style={styles.section}>
                <Text style={styles.label}>Driving hours: {hours}h</Text>
                <Slider
                  style={styles.slider}
                  minimumValue={1}
                  maximumValue={24}
                  step={1}
                  value={hours}
                  onValueChange={setHours}
                  minimumTrackTintColor="#000"
                  maximumTrackTintColor="#E5E5E5"
                  thumbTintColor="#000"
                />
                <View style={styles.sliderLabels}>
                  <Text style={styles.sliderLabel}>1h</Text>
                  <Text style={styles.sliderLabel}>24h</Text>
                </View>
              </View>

              <TouchableOpacity
                style={[
                  styles.continueButton,
                  (startIndex === null || endIndex === null || isLoading) &&
                    styles.continueButtonDisabled,
                ]}
                onPress={async () => {
                  if (startIndex !== null && endIndex !== null && !isLoading) {
                    try {
                      setIsLoading(true);

                      // Save preferences to backend
                      await saveWorkingHours(Config.DEFAULT_DRIVER_ID, {
                        earliest_start_time: TIME_SLOTS[startIndex],
                        latest_start_time: TIME_SLOTS[endIndex],
                        nr_hours: Math.round(hours), // Ensure integer value
                      });

                      const optimalResponse = await getOptimalTime(Config.DEFAULT_DRIVER_ID);
                      const optimalTimeString = hourToTimeString(optimalResponse.optimal_time);

                      onSchedule(
                        optimalTimeString,
                        optimalResponse.optimal_time,
                        Math.round(hours),
                      );
                    } catch (error) {
                      console.error("Failed to save preferences:", error);
                      Alert.alert("Error", "Failed to save preferences. Please try again.");
                    } finally {
                      setIsLoading(false);
                    }
                  }
                }}
                disabled={startIndex === null || endIndex === null || isLoading}
                activeOpacity={0.8}
              >
                <Text style={styles.continueText}>
                  {isLoading ? "Loading..." : "Get Recommendations"}
                </Text>
              </TouchableOpacity>
            </View>
          </View>
        </Animated.View>
      </TouchableOpacity>
    </Modal>
  );
}

const styles = StyleSheet.create({
  backdrop: {
    flex: 1,
    backgroundColor: "rgba(0,0,0,0.5)",
    justifyContent: "flex-end",
  },
  container: {
    backgroundColor: "#fff",
    borderTopLeftRadius: 16,
    borderTopRightRadius: 16,
    paddingBottom: 30,
    shadowColor: "#000",
    shadowOffset: { width: 0, height: -2 },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 5,
  },
  handle: {
    alignItems: "center",
    paddingVertical: 12,
  },
  handleBar: {
    width: 40,
    height: 4,
    backgroundColor: "#D1D1D6",
    borderRadius: 2,
  },
  content: {
    paddingHorizontal: 20,
  },
  title: {
    fontSize: 24,
    fontWeight: "700",
    marginBottom: 20,
    color: "#000",
  },
  section: {
    marginBottom: 20,
  },
  label: {
    fontSize: 16,
    fontWeight: "600",
    marginBottom: 12,
    color: "#000",
  },
  timeGrid: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 8,
  },
  timeSlot: {
    backgroundColor: "#F2F2F7",
    paddingVertical: 8,
    paddingHorizontal: 10,
    borderRadius: 6,
    minWidth: 60,
    alignItems: "center",
  },
  timeSlotInRange: {
    backgroundColor: "#000",
  },
  timeSlotSelected: {
    backgroundColor: "#000",
  },
  timeSlotText: {
    fontSize: 13,
    fontWeight: "500",
    color: "#000",
  },
  timeSlotTextInRange: {
    color: "#fff",
    fontWeight: "600",
  },
  timeSlotTextSelected: {
    color: "#fff",
    fontWeight: "700",
  },
  slider: {
    width: "100%",
    height: 40,
  },
  sliderLabels: {
    flexDirection: "row",
    justifyContent: "space-between",
    marginTop: 4,
  },
  sliderLabel: {
    fontSize: 14,
    color: "#8E8E93",
  },
  continueButton: {
    backgroundColor: "#000",
    padding: 16,
    borderRadius: 12,
    alignItems: "center",
    marginTop: 10,
  },
  continueButtonDisabled: {
    backgroundColor: "#C7C7CC",
  },
  continueText: {
    color: "#fff",
    fontWeight: "600",
    fontSize: 17,
  },
});
