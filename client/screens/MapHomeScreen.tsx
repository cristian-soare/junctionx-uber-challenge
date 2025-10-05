import { Ionicons } from "@expo/vector-icons";
import { useNavigation } from "@react-navigation/native";
import * as Location from "expo-location";
import React, { useEffect, useState } from "react";
import { Alert, StyleSheet, Text, TouchableOpacity, View } from "react-native";
import MapView, { Marker, Region } from "react-native-maps";
import { SafeAreaView } from "react-native-safe-area-context";
import DriverStatus from "../components/DriverStatus";
import SchedulePanel from "../components/SchedulePanel";
import WellnessNudge from "../components/WellnessNudge";
import OptimalDetailsPanel from "../components/OptimalDetailsPanel";

export default function MapHomeScreen() {
  const navigation = useNavigation<any>();
  const [location, setLocation] = useState<Region | null>(null);
  const [isOnline, setIsOnline] = useState(false);
  const [isScheduleOpen, setIsScheduleOpen] = useState(false);
  const [showConfirmDialog, setShowConfirmDialog] = useState(false);
  const [isOptimalDetailsOpen, setIsOptimalDetailsOpen] = useState(false);
  const [optimalTime, setOptimalTime] = useState<string | null>(null);
  const [optimalTimeHour, setOptimalTimeHour] = useState<number | null>(null);
  const [nrHours, setNrHours] = useState<number | null>(null);
  const [earnings, setEarnings] = useState(247.50);
  const [currentTime, setCurrentTime] = useState(new Date());
  const [progressWidth, setProgressWidth] = useState(0);
  const [remainingTime, setRemainingTime] = useState<number | null>(null);
  const [wellnessNudgeDismissed, setWellnessNudgeDismissed] = useState(false);
  const [scheduleStartTime, setScheduleStartTime] = useState<number | null>(null);

  // 🧠 Start at 4:29:55 (for testing) - keeping for backwards compatibility
  const [drivingSeconds, setDrivingSeconds] = useState(4 * 3600 + 29 * 60 + 55);

  // 📍 Track location
  useEffect(() => {
    (async () => {
      let { status } = await Location.requestForegroundPermissionsAsync();
      if (status !== "granted") return;

      const loc = await Location.getCurrentPositionAsync({});
      setLocation({
        latitude: loc.coords.latitude,
        longitude: loc.coords.longitude,
        latitudeDelta: 0.05,
        longitudeDelta: 0.05,
      });
    })();
  }, []);

  // ⏱ Track driving time - Update hours from server periodically
  useEffect(() => {
    let timer: NodeJS.Timeout | null = null;
    let hoursTimer: NodeJS.Timeout | null = null;

    if (isOnline) {
      timer = setInterval(() => {
        setDrivingSeconds((prev) => prev + 1);
      }, 1000);

      // Fetch hours from server every 30 seconds
      hoursTimer = setInterval(async () => {
        try {
          const data = await getDrivingHours(Config.DEFAULT_DRIVER_ID);
          setHoursToday(data.total_hours_today);
        } catch (error) {
          console.error("Failed to fetch driving hours:", error);
        }
      }, 30000);

      // Fetch immediately when going online
      getDrivingHours(Config.DEFAULT_DRIVER_ID)
        .then((data) => setHoursToday(data.total_hours_today))
        .catch((error) => console.error("Failed to fetch driving hours:", error));
    }

    return () => {
      if (timer) clearInterval(timer);
      if (hoursTimer) clearInterval(hoursTimer);
    };
  }, [isOnline]);

  // Schedule button is always enabled to allow setting multiple preferences

  // Update current time every second
  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentTime(new Date());
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  // Calculate progress bar width when optimal time is set (fills up in 60 seconds for demo)
  useEffect(() => {
    if (optimalTime && !isOnline && scheduleStartTime) {
      // Progress fills up in 60 seconds (demo) - smooth and constant
      const now = Date.now();
      const elapsedMs = now - scheduleStartTime;
      const elapsedSeconds = elapsedMs / 1000;
      const progress = Math.min(100, (elapsedSeconds / 60) * 100);
      setProgressWidth(progress);
    } else if (!optimalTime || isOnline) {
      setProgressWidth(0);
      setScheduleStartTime(null);
    }
  }, [currentTime, optimalTime, isOnline, scheduleStartTime]);

  // Countdown remaining time when online
  useEffect(() => {
    if (isOnline) {
      if (remainingTime === null) {
        // Initialize with 5 hours for demo (18000 seconds = 5:00:00)
        setRemainingTime(18000);
      } else if (remainingTime > 0) {
        // Decrement every second
        const timer = setTimeout(() => {
          setRemainingTime(remainingTime - 1);
        }, 1000);
        return () => clearTimeout(timer);
      }
    }
  }, [isOnline, remainingTime]);

  if (!location)
    return (
      <View style={styles.loading}>
        <Text>Loading map...</Text>
      </View>
    );

  return (
    <SafeAreaView style={styles.container} edges={['top']}>
      {/* Map */}
      <MapView style={StyleSheet.absoluteFillObject} region={location}>
        <Marker coordinate={location} title="You">
          <View style={styles.markerContainer}>
            <View style={styles.markerCircle}>
              <Ionicons name="arrow-up" size={20} color="#000" />
            </View>
          </View>
        </Marker>
      </MapView>

      {/* Top Bar - Settings, Earnings, Search */}
      <View style={styles.topBar}>
        <TouchableOpacity style={styles.settingsButtonTop}>
          <Ionicons name="settings-outline" size={24} color="#000" />
        </TouchableOpacity>
        <View style={styles.earningsContainer}>
          <Text style={styles.earningsAmount}>${earnings.toFixed(2)}</Text>
        </View>
        <TouchableOpacity style={styles.searchButton}>
          <Ionicons name="search" size={24} color="#000" />
        </TouchableOpacity>
      </View>

      {/* Floating UI */}
      {!isScheduleOpen && (
        <View style={styles.bottomUI}>
          <View style={styles.buttonRow}>
            {/* GO/STOP button */}
            <TouchableOpacity
              style={[styles.actionButton, isOnline ? styles.stopButton : styles.goButton]}
              onPress={() => {
                if (isOnline) {
                  // STOP: reset to offline and clear schedule
                  setIsOnline(false);
                  setRemainingTime(null);
                  setWellnessNudgeDismissed(true);
                  setOptimalTime(null);
                  setScheduleStartTime(null);
                } else {
                  // GO: if scheduled, go directly online; otherwise show dialog
                  if (optimalTime) {
                    setIsOnline(true);
                  } else {
                    setShowConfirmDialog(true);
                  }
                }
              }}
            >
              <View style={styles.actionButtonInner}>
                <Text style={styles.actionButtonText}>{isOnline ? "STOP" : "GO"}</Text>
              </View>
            </TouchableOpacity>

            {/* Schedule button */}
            <TouchableOpacity
              style={[
                styles.actionButton,
                styles.scheduleActionButton,
              ]}
              onPress={() => setIsScheduleOpen(true)}
            >
              <View style={styles.actionButtonInner}>
                <Ionicons name="calendar-outline" size={28} color="#fff" />
              </View>
            </TouchableOpacity>
          </View>

          {/* Status bar */}
          {optimalTime && !isOnline ? (
            <View style={styles.optimalBar}>
              <View style={[styles.progressBar, { width: `${progressWidth}%` }]} />
              <TouchableOpacity
                style={styles.timeContainer}
                onPress={() => setIsOptimalDetailsOpen(true)}
                activeOpacity={0.8}
              >
                <Text style={styles.optimalText}>{optimalTime}</Text>
              </TouchableOpacity>
            </View>
          ) : isOnline && remainingTime !== null ? (
            <View style={styles.statusBarOnline}>
              <Text style={styles.statusTextOnline}>
                {Math.floor(remainingTime / 3600)}:{String(Math.floor((remainingTime % 3600) / 60)).padStart(2, '0')}:{String(remainingTime % 60).padStart(2, '0')}
              </Text>
            </View>
          ) : (
            <View style={styles.statusBar}>
              <Text style={styles.statusText}>{isOnline ? "Online" : "Offline"}</Text>
            </View>
          )}
        </View>
      )}

      {/* Confirm Dialog */}
      {showConfirmDialog && (
        <View style={styles.dialogOverlay}>
          <View style={styles.dialogBox}>
            <Text style={styles.dialogTitle}>Start Driving?</Text>
            <Text style={styles.dialogMessage}>
              Are you ready to go online?
            </Text>
            <View style={styles.dialogButtons}>
              <TouchableOpacity
                style={styles.dialogButtonConfirm}
                onPress={() => {
                  setIsOnline(true);
                  setShowConfirmDialog(false);
                }}
              >
                <Text style={styles.dialogButtonConfirmText}>Go Now</Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={styles.dialogButtonCancel}
                onPress={() => setShowConfirmDialog(false)}
              >
                <Text style={styles.dialogButtonCancelText}>Cancel</Text>
              </TouchableOpacity>
            </View>
          </View>
        </View>
      )}

      {/* Schedule panel */}
      <SchedulePanel
        visible={isScheduleOpen}
        onClose={() => setIsScheduleOpen(false)}
        onSchedule={(time, optimalTimeHour, nrHours) => {
          setOptimalTime(time);
          setOptimalTimeHour(optimalTimeHour);
          setNrHours(nrHours);
          setIsScheduleOpen(false);
          setScheduleStartTime(Date.now());
        }}
      />

      {/* 🚨 Wellness Nudge */}
      {/* <WellnessNudge
        drivingSeconds={drivingSeconds}
        onOpenCopilot={() => navigation.navigate("Copilot")}
        isDismissed={wellnessNudgeDismissed}
        onDismiss={() => setWellnessNudgeDismissed(true)}
      />

      {/* Optimal Details Panel */}
      {optimalTime && (
        <OptimalDetailsPanel
          visible={isOptimalDetailsOpen}
          onClose={() => setIsOptimalDetailsOpen(false)}
          optimalTime={optimalTime}
          optimalTimeHour={optimalTimeHour}
          nrHours={nrHours}
          onTimeChange={(newTime) => {
            setOptimalTime(newTime);
            setScheduleStartTime(Date.now());
          }}
        />
      )}
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  loading: {
    flex: 1,
    justifyContent: "center",
    alignItems: "center",
  },
  topBar: {
    position: "absolute",
    top: 60,
    left: 20,
    right: 20,
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    zIndex: 10,
  },
  settingsButtonTop: {
    backgroundColor: "#fff",
    width: 44,
    height: 44,
    borderRadius: 22,
    justifyContent: "center",
    alignItems: "center",
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.25,
    shadowRadius: 4,
    elevation: 5,
  },
  earningsContainer: {
    backgroundColor: "#fff",
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 20,
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.25,
    shadowRadius: 4,
    elevation: 5,
    position: "absolute",
    left: "50%",
    transform: [{ translateX: -50 }],
  },
  earningsAmount: {
    fontSize: 18,
    fontWeight: "700",
    color: "#34C759",
  },
  searchButton: {
    backgroundColor: "#fff",
    width: 44,
    height: 44,
    borderRadius: 22,
    justifyContent: "center",
    alignItems: "center",
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.25,
    shadowRadius: 4,
    elevation: 5,
  },
  markerContainer: {
    alignItems: "center",
    justifyContent: "center",
  },
  markerCircle: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: "#fff",
    justifyContent: "center",
    alignItems: "center",
    borderWidth: 3,
    borderColor: "#000",
  },
  topContainer: {
    position: "absolute",
    top: 60,
    left: 0,
    right: 0,
    zIndex: 1,
  },
  aiChatButton: {
    position: "absolute",
    top: 200,
    right: 20,
    backgroundColor: "#007AFF",
    width: 56,
    height: 56,
    borderRadius: 28,
    justifyContent: "center",
    alignItems: "center",
    elevation: 4,
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.25,
    shadowRadius: 4,
    zIndex: 1,
  },
  bottomUI: {
    position: "absolute",
    bottom: 0,
    width: "100%",
    alignItems: "center",
  },
  buttonRow: {
    flexDirection: "row",
    gap: 20,
    marginBottom: 24,
  },
  actionButton: {
    width: 80,
    height: 80,
    borderRadius: 40,
    justifyContent: "center",
    alignItems: "center",
    elevation: 5,
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.25,
    shadowRadius: 4,
    padding: 4,
  },
  actionButtonInner: {
    width: "100%",
    height: "100%",
    borderRadius: 36,
    borderWidth: 3,
    borderColor: "#fff",
    justifyContent: "center",
    alignItems: "center",
  },
  goButton: {
    backgroundColor: "#007AFF",
  },
  stopButton: {
    backgroundColor: "#E11900",
  },
  scheduleActionButton: {
    backgroundColor: "#34C759",
  },
  scheduleButtonDisabled: {
    backgroundColor: "#A0A0A0",
    opacity: 0.5,
  },
  actionButtonText: {
    color: "#fff",
    fontSize: 18,
    fontWeight: "bold",
  },
  statusBar: {
    width: "100%",
    backgroundColor: "#fff",
    paddingTop: 18,
    paddingHorizontal: 20,
    justifyContent: "center",
    alignItems: "center",
    borderTopWidth: 1,
    borderTopColor: "#E0E0E0",
    shadowColor: "#000",
    shadowOffset: { width: 0, height: -3 },
    shadowOpacity: 0.2,
    shadowRadius: 6,
    elevation: 8,
    paddingBottom: 30,
    minHeight: 90,
  },
  statusText: {
    fontSize: 28,
    fontWeight: "700",
    color: "#000",
  },
  timeContainer: {
    backgroundColor: "#fff",
    paddingHorizontal: 24,
    paddingVertical: 12,
    borderRadius: 12,
    borderWidth: 4,
    borderColor: "#fff",
    zIndex: 1,
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.15,
    shadowRadius: 4,
    elevation: 3,
  },
  statusBarOnline: {
    width: "100%",
    backgroundColor: "#000",
    paddingTop: 18,
    paddingHorizontal: 20,
    justifyContent: "center",
    alignItems: "center",
    borderTopWidth: 1,
    borderTopColor: "#333",
    shadowColor: "#000",
    shadowOffset: { width: 0, height: -3 },
    shadowOpacity: 0.2,
    shadowRadius: 6,
    elevation: 8,
    paddingBottom: 30,
    minHeight: 90,
  },
  statusTextOnline: {
    fontSize: 32,
    fontWeight: "700",
    color: "#fff",
    textShadowColor: "rgba(255, 255, 255, 0.8)",
    textShadowOffset: { width: 0, height: 0 },
    textShadowRadius: 15,
  },
  optimalBar: {
    width: "100%",
    backgroundColor: "#fff",
    paddingTop: 18,
    paddingHorizontal: 20,
    justifyContent: "center",
    alignItems: "center",
    shadowColor: "#000",
    shadowOffset: { width: 0, height: -3 },
    shadowOpacity: 0.2,
    shadowRadius: 6,
    elevation: 8,
    paddingBottom: 30,
    minHeight: 90,
    overflow: "hidden",
    position: "relative",
    borderTopWidth: 1,
    borderTopColor: "#E0E0E0",
  },
  progressBar: {
    position: "absolute",
    left: 0,
    top: 0,
    bottom: 0,
    backgroundColor: "#34C759",
    zIndex: 0,
  },
  optimalText: {
    fontSize: 30,
    fontWeight: "700",
    color: "#000",
  },
  dialogOverlay: {
    position: "absolute",
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: "rgba(0,0,0,0.5)",
    justifyContent: "center",
    alignItems: "center",
  },
  dialogBox: {
    backgroundColor: "#fff",
    borderRadius: 16,
    padding: 24,
    width: "85%",
    maxWidth: 400,
  },
  dialogTitle: {
    fontSize: 18,
    fontWeight: "700",
    marginBottom: 10,
    color: "#000",
  },
  dialogMessage: {
    fontSize: 14,
    color: "#333",
    marginBottom: 20,
    lineHeight: 20,
  },
  dialogButtons: {
    flexDirection: "row",
    gap: 12,
  },
  dialogButtonCancel: {
    flex: 1,
    padding: 14,
    borderRadius: 10,
    backgroundColor: "#F2F2F7",
    alignItems: "center",
  },
  dialogButtonCancelText: {
    fontSize: 14,
    fontWeight: "600",
    color: "#000",
  },
  dialogButtonConfirm: {
    flex: 1,
    padding: 14,
    borderRadius: 10,
    backgroundColor: "#007AFF",
    alignItems: "center",
  },
  dialogButtonConfirmText: {
    fontSize: 14,
    fontWeight: "600",
    color: "#fff",
  },
});
