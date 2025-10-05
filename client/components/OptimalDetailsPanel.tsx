import React, { useEffect, useRef, useState } from "react";
import { Text, TouchableOpacity, View, StyleSheet, Modal, Animated, Dimensions, ScrollView } from "react-native";
import { getTimeScores, getBestZone } from "../services/preferencesService";
import { TimeScore, BestZoneResponse } from "../models/api";
import { hourToTimeString, timeStringToHour } from "../models/api";
import Config from "../config/Config";

interface OptimalDetailsPanelProps {
  visible: boolean;
  onClose: () => void;
  optimalTime: string;
  optimalTimeHour: number | null;
  nrHours: number | null;
  onTimeChange: (newTime: string) => void;
}

const SCREEN_HEIGHT = Dimensions.get("window").height;
const SCREEN_WIDTH = Dimensions.get("window").width;
const ITEM_WIDTH = 50;

export default function OptimalDetailsPanel({ visible, onClose, optimalTime, optimalTimeHour, nrHours, onTimeChange }: OptimalDetailsPanelProps) {
  const slideAnim = useRef(new Animated.Value(SCREEN_HEIGHT)).current;
  const [showTimeDetails, setShowTimeDetails] = useState(false);
  const [showZoneDetails, setShowZoneDetails] = useState(false);
  const [selectedTimeIndex, setSelectedTimeIndex] = useState(0);
  const scrollViewRef = useRef<ScrollView>(null);
  const [timeSlots, setTimeSlots] = useState<Array<{id: string, timeShort: string, timeFull: string, optimality: number, hour: number}>>([]);
  const [bestZone, setBestZone] = useState<BestZoneResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const barHeightsRef = useRef<Animated.Value[]>([]);
  const paddingSide = (SCREEN_WIDTH - ITEM_WIDTH) / 2;

  useEffect(() => {
    if (visible) {
      slideAnim.setValue(SCREEN_HEIGHT);
      Animated.spring(slideAnim, {
        toValue: 0,
        useNativeDriver: true,
        tension: 65,
        friction: 11,
      }).start();

      fetchData();
    } else {
      Animated.timing(slideAnim, {
        toValue: SCREEN_HEIGHT,
        duration: 300,
        useNativeDriver: true,
      }).start();
      setShowTimeDetails(false);
      setShowZoneDetails(false);
    }
  }, [visible]);

  const fetchData = async () => {
    try {
      setIsLoading(true);

      const timeScoresResponse = await getTimeScores(Config.DEFAULT_DRIVER_ID);

      const bestZoneResponse = optimalTimeHour !== null
        ? await getBestZone(Config.DEFAULT_DRIVER_ID, optimalTimeHour)
        : null;

      const slots = timeScoresResponse.scores.map((score: TimeScore) => ({
        id: `slot-${score.time}`,
        timeShort: `${String(score.time).padStart(2, '0')}`,
        timeFull: hourToTimeString(score.time),
        optimality: Math.round(score.score * 100),
        hour: score.time
      }));

      setTimeSlots(slots);
      setBestZone(bestZoneResponse);
      barHeightsRef.current = slots.map(() => new Animated.Value(0));
    } catch (error) {
      console.error("Failed to fetch optimal details:", error);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (showTimeDetails && timeSlots.length > 0) {
      const animations = timeSlots.map((slot, idx) => {
        const finalHeight = (slot.optimality / 100) * 320 + 80;
        return Animated.timing(barHeightsRef.current[idx], {
          toValue: finalHeight,
          duration: 500,
          useNativeDriver: false,
        });
      });
      Animated.stagger(40, animations).start();
      const targetX = Math.max(0, Math.min(timeSlots.length - 1, selectedTimeIndex)) * ITEM_WIDTH;
      setTimeout(() => {
        scrollViewRef.current?.scrollTo({ x: targetX, animated: true });
      }, 60);
    } else if (timeSlots.length > 0) {
      timeSlots.forEach((_, idx) => barHeightsRef.current[idx]?.setValue(0));
    }
  }, [showTimeDetails, selectedTimeIndex, timeSlots]);

  if (!visible) return null;

  const handleMomentumScrollEnd = (event: any) => {
    const offsetX = event.nativeEvent.contentOffset.x;
    const index = Math.max(0, Math.min(timeSlots.length - 1, Math.round(offsetX / ITEM_WIDTH)));
    setSelectedTimeIndex(index);
  };

  const handleConfirmTime = () => {
    const newTime = timeSlots[selectedTimeIndex]?.timeFull ?? optimalTime;
    onTimeChange(newTime);
    setShowTimeDetails(false);
  };

  if (showTimeDetails) {
    return (
      <Modal visible={true} animationType="none" transparent>
        <View style={styles.backdrop}>
          <View style={styles.fullContainer}>
            <TouchableOpacity
              style={styles.backButton}
              onPress={() => setShowTimeDetails(false)}
            >
              <Text style={styles.backButtonText}>← Back</Text>
            </TouchableOpacity>
            <Text style={styles.detailTitle}>Select Optimal Time</Text>

            {/* Bar Chart Time Selector */}
            <View style={styles.chartContainer}>
              <ScrollView
                ref={scrollViewRef}
                horizontal
                showsHorizontalScrollIndicator={false}
                snapToInterval={ITEM_WIDTH}
                snapToAlignment="center"
                decelerationRate="normal" // smoother deceleration
                contentContainerStyle={[styles.scrollContent, { paddingHorizontal: paddingSide }]}
                onMomentumScrollEnd={handleMomentumScrollEnd}
                scrollEventThrottle={16}
              >
                {timeSlots.length > 0 ? timeSlots.map((slot, index) => {
                  const isSelected = index === selectedTimeIndex;
                  const animatedHeight = barHeightsRef.current[index];
                  const barColor = slot.optimality > 66 ? "#34C759" : slot.optimality > 33 ? "#FF9500" : "#E0E0E0";

                  return (
                    <View key={slot.id} style={styles.barItem}>
                      <Text style={[styles.hoursLabel, isSelected && styles.hoursLabelSelected]}>
                        {slot.timeFull}
                      </Text>
                      <Text style={styles.percentLabel}>{slot.optimality}%</Text>

                      <Animated.View
                        style={[
                          styles.bar,
                          {
                            height: animatedHeight,
                            backgroundColor: isSelected ? "#007AFF" : barColor,
                          },
                          isSelected && styles.barSelected,
                        ]}
                      />
                      <Text style={[styles.timeLabel, isSelected && styles.timeLabelSelected]}>
                        {slot.timeShort}
                      </Text>
                    </View>
                  );
                }) : (
                  <View style={styles.loadingContainer}>
                    <Text style={styles.loadingText}>Loading...</Text>
                  </View>
                )}
              </ScrollView>

              {/* center indicator removed */}
            </View>

            <TouchableOpacity
              style={styles.confirmButton}
              onPress={handleConfirmTime}
            >
              <Text style={styles.confirmButtonText}>Confirm Time</Text>
            </TouchableOpacity>
          </View>
        </View>
      </Modal>
    );
  }

  if (showZoneDetails) {
    return (
      <Modal visible={true} animationType="none" transparent>
        <View style={styles.backdrop}>
          <View style={styles.fullContainer}>
            <TouchableOpacity
              style={styles.backButton}
              onPress={() => setShowZoneDetails(false)}
            >
              <Text style={styles.backButtonText}>← Back</Text>
            </TouchableOpacity>
            <Text style={styles.detailTitle}>Zone Details</Text>
            {/* TODO: Add zone details content */}
          </View>
        </View>
      </Modal>
    );
  }

  return (
    <Modal
      visible={visible}
      transparent
      animationType="none"
      onRequestClose={onClose}
    >
      <View style={styles.backdrop}>
        <Animated.View
          style={[
            styles.container,
            {
              transform: [{ translateY: slideAnim }],
            },
          ]}
        >
          <View style={styles.content}>
            <Text style={styles.title}>Optimal Schedule</Text>

            {/* Optimal Time */}
            <TouchableOpacity
              style={styles.timeContainer}
              onPress={() => setShowTimeDetails(true)}
              activeOpacity={0.7}
            >
              <Text style={styles.timeLabel}>Optimal Start Time</Text>
              <View style={styles.timeBox}>
                <Text style={styles.timeText}>{optimalTime}</Text>
              </View>
            </TouchableOpacity>

            {/* Optimal Zone */}
            <TouchableOpacity
              style={styles.zoneContainer}
              onPress={() => setShowZoneDetails(true)}
              activeOpacity={0.7}
            >
              <Text style={styles.zoneLabel}>Optimal Zone</Text>
              <View style={styles.zoneBox}>
                <Text style={styles.zoneText}>
                  {isLoading ? "Loading..." : bestZone?.cluster_id ? `${bestZone.cluster_id}` : "No zone"}
                </Text>
              </View>
            </TouchableOpacity>

            <TouchableOpacity
              style={styles.closeButton}
              onPress={onClose}
            >
              <Text style={styles.closeButtonText}>Close</Text>
            </TouchableOpacity>
          </View>
        </Animated.View>
      </View>
    </Modal>
  );
}

const styles = StyleSheet.create({
  backdrop: {
    flex: 1,
    backgroundColor: "rgba(0,0,0,0.5)",
  },
  container: {
    flex: 1,
    backgroundColor: "#fff",
    paddingTop: 60,
  },
  fullContainer: {
    flex: 1,
    backgroundColor: "#fff",
    paddingTop: 60,
    paddingHorizontal: 20,
  },
  content: {
    flex: 1,
    paddingHorizontal: 20,
    paddingTop: 20,
  },
  title: {
    fontSize: 32,
    fontWeight: "700",
    marginBottom: 40,
    color: "#000",
    textAlign: "center",
  },
  chartContainer: {
    flex: 1,
    marginTop: 40,
    position: "relative",
  },
  scrollContent: {
    alignItems: "flex-end",
    paddingBottom: 20,
  },
  barItem: {
    width: ITEM_WIDTH,
    alignItems: "center",
    justifyContent: "flex-end",
  },
  hoursLabel: {
    // larger and more visible
    fontSize: 12,
    color: "#000",
    fontWeight: "700",
    marginBottom: 6,
    // subtle shadow to increase legibility
    textShadowColor: "rgba(0,0,0,0.12)",
    textShadowOffset: { width: 0, height: 1 },
    textShadowRadius: 1,
  },
  hoursLabelSelected: {
    color: "#000",
    fontWeight: "800",
  },
  percentLabel: {
    fontSize: 13,
    color: "#000",
    fontWeight: "700",
    marginBottom: 8,
    textShadowColor: "rgba(0,0,0,0.12)",
    textShadowOffset: { width: 0, height: 1 },
    textShadowRadius: 1,
  },
  bar: {
    // slightly wider and keep rounded top
    width: 44, // was 40
    borderRadius: 10,
    borderTopLeftRadius: 10,
    borderTopRightRadius: 10,
  },
  barSelected: {
    shadowColor: "#007AFF",
    shadowOffset: { width: 0, height: 6 },
    shadowOpacity: 0.12,
    shadowRadius: 8,
    elevation: 4,
  },
  timeLabel: {
    fontSize: 12,
    fontWeight: "600",
    color: "#999",
    marginTop: 10,
  },
  timeLabelSelected: {
    fontSize: 14,
    fontWeight: "700",
    color: "#000",
  },

  confirmButton: {
    backgroundColor: "#000",
    padding: 16,
    borderRadius: 12,
    alignItems: "center",
    marginBottom: 40,
  },
  confirmButtonText: {
    color: "#fff",
    fontWeight: "600",
    fontSize: 17,
  },
  timeContainer: {
    marginBottom: 30,
    alignItems: "center",
  },
  timeBox: {
    backgroundColor: "#fff",
    paddingHorizontal: 32,
    paddingVertical: 16,
    borderRadius: 12,
    borderWidth: 4,
    borderColor: "#fff",
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.15,
    shadowRadius: 4,
    elevation: 3,
  },
  timeText: {
    fontSize: 36,
    fontWeight: "700",
    color: "#000",
  },
  zoneContainer: {
    marginBottom: 30,
    alignItems: "center",
  },
  zoneLabel: {
    fontSize: 18,
    fontWeight: "600",
    color: "#666",
    marginBottom: 12,
  },
  zoneBox: {
    backgroundColor: "#87CEEB",
    paddingHorizontal: 40,
    paddingVertical: 20,
    borderRadius: 16,
    borderWidth: 4,
    borderColor: "#fff",
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.25,
    shadowRadius: 4,
    elevation: 5,
  },
  zoneText: {
    fontSize: 28,
    fontWeight: "700",
    color: "#fff",
  },
  closeButton: {
    backgroundColor: "#000",
    padding: 16,
    borderRadius: 12,
    alignItems: "center",
    marginTop: "auto",
    marginBottom: 40,
  },
  closeButtonText: {
    color: "#fff",
    fontWeight: "600",
    fontSize: 17,
  },
  backButton: {
    padding: 12,
    alignSelf: "flex-start",
    marginBottom: 20,
  },
  backButtonText: {
    fontSize: 18,
    fontWeight: "600",
    color: "#007AFF",
  },
  detailTitle: {
    fontSize: 28,
    fontWeight: "700",
    marginBottom: 20,
    color: "#000",
  },
  loadingContainer: {
    flex: 1,
    justifyContent: "center",
    alignItems: "center",
    paddingVertical: 40,
  },
  loadingText: {
    fontSize: 16,
    color: "#999",
  },
});
