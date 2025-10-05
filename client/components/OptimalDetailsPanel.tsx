import React, { useEffect, useRef, useState } from "react";
import { Text, TouchableOpacity, View, StyleSheet, Modal, Animated, Dimensions } from "react-native";

interface OptimalDetailsPanelProps {
  visible: boolean;
  onClose: () => void;
  optimalTime: string;
}

const SCREEN_HEIGHT = Dimensions.get("window").height;

export default function OptimalDetailsPanel({ visible, onClose, optimalTime }: OptimalDetailsPanelProps) {
  const slideAnim = useRef(new Animated.Value(SCREEN_HEIGHT)).current;
  const [showTimeDetails, setShowTimeDetails] = useState(false);
  const [showZoneDetails, setShowZoneDetails] = useState(false);

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
      // Reset when closing
      setShowTimeDetails(false);
      setShowZoneDetails(false);
    }
  }, [visible]);

  if (!visible) return null;

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
            <Text style={styles.detailTitle}>Time Details</Text>
            {/* TODO: Add time details content */}
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
                <Text style={styles.zoneText}>Z4 (Zone 4)</Text>
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
  timeContainer: {
    marginBottom: 30,
    alignItems: "center",
  },
  timeLabel: {
    fontSize: 18,
    fontWeight: "600",
    color: "#666",
    marginBottom: 12,
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
});
