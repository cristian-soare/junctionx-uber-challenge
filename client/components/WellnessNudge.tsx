import React, { useEffect, useState } from "react";
import { Modal, StyleSheet, Text, TouchableOpacity, View } from "react-native";

interface WellnessNudgeProps {
  drivingSeconds: number;
  onOpenCopilot: () => void;
  isDismissed: boolean;
  onDismiss: () => void;
}

export default function WellnessNudge({ drivingSeconds, onOpenCopilot, isDismissed, onDismiss }: WellnessNudgeProps) {
  const [showNudge, setShowNudge] = useState(false);
  const [hasShown, setHasShown] = useState(false);

  useEffect(() => {
    // Show nudge at 4h 30m (16200 seconds) only once
    if (drivingSeconds >= 16200 && !hasShown && !isDismissed) {
      setShowNudge(true);
      setHasShown(true);
    }
  }, [drivingSeconds, hasShown, isDismissed]);

  if (!showNudge || isDismissed) return null;

  return (
    <Modal visible={showNudge} animationType="fade" transparent>
      <View style={styles.overlay}>
        <View style={styles.card}>
          <Text style={styles.emoji}>⚠️</Text>
          <Text style={styles.title}>Time for a Break</Text>
          <Text style={styles.message}>
            You've been driving for 4.5 hours. Taking a break now can help you stay alert and safe on the road.
          </Text>
          <TouchableOpacity
            style={styles.button}
            onPress={() => {
              setShowNudge(false);
              onDismiss();
              onOpenCopilot();
            }}
          >
            <Text style={styles.buttonText}>Open Wellness Copilot</Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={styles.dismissButton}
            onPress={() => {
              setShowNudge(false);
              onDismiss();
            }}
          >
            <Text style={styles.dismissText}>I'll take a break soon</Text>
          </TouchableOpacity>
        </View>
      </View>
    </Modal>
  );
}

const styles = StyleSheet.create({
  overlay: {
    flex: 1,
    backgroundColor: "rgba(0,0,0,0.7)",
    justifyContent: "center",
    alignItems: "center",
    padding: 20,
  },
  card: {
    backgroundColor: "#fff",
    borderRadius: 20,
    padding: 30,
    width: "100%",
    maxWidth: 400,
    alignItems: "center",
  },
  emoji: {
    fontSize: 48,
    marginBottom: 15,
  },
  title: {
    fontSize: 24,
    fontWeight: "bold",
    marginBottom: 15,
    textAlign: "center",
  },
  message: {
    fontSize: 16,
    color: "#333",
    marginBottom: 25,
    lineHeight: 24,
    textAlign: "center",
  },
  button: {
    backgroundColor: "#007AFF",
    padding: 16,
    borderRadius: 12,
    alignItems: "center",
    width: "100%",
    marginBottom: 12,
  },
  buttonText: {
    color: "#fff",
    fontSize: 17,
    fontWeight: "600",
  },
  dismissButton: {
    padding: 12,
    alignItems: "center",
  },
  dismissText: {
    color: "#666",
    fontSize: 16,
  },
});
