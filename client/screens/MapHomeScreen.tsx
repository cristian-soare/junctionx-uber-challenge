import { Ionicons } from "@expo/vector-icons";
import { useNavigation } from "@react-navigation/native";
import * as Location from "expo-location";
import React, { useEffect, useState } from "react";
import { StyleSheet, Text, TouchableOpacity, View } from "react-native";
import MapView, { Marker, Region } from "react-native-maps";
import { SafeAreaView } from "react-native-safe-area-context";
import DriverStatus from "../components/DriverStatus";
import SchedulePanel from "../components/SchedulePanel";
import WellnessNudge from "../components/WellnessNudge";

export default function MapHomeScreen() {
  const navigation = useNavigation<any>();
  const [location, setLocation] = useState<Region | null>(null);
  const [isOnline, setIsOnline] = useState(false);
  const [isScheduleOpen, setIsScheduleOpen] = useState(false);

  // 🧠 Start at 4:29:55 (for testing)
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

  // ⏱ Track driving time
  useEffect(() => {
    let timer: NodeJS.Timeout | null = null;

    if (isOnline) {
      timer = setInterval(() => {
        setDrivingSeconds((prev) => prev + 1);
      }, 1000);
    }

    return () => {
      if (timer) clearInterval(timer);
    };
  }, [isOnline]);

  if (!location)
    return (
      <View style={styles.loading}>
        <Text>Loading map...</Text>
      </View>
    );

  return (
    <SafeAreaView style={styles.container}>
      {/* Map */}
      <MapView style={StyleSheet.absoluteFillObject} region={location}>
        <Marker coordinate={location} title="You" pinColor="blue" />
      </MapView>

      {/* Floating UI */}
      {!isScheduleOpen && (
        <View style={styles.bottomUI}>
          {/* GO / STOP button */}
          <TouchableOpacity
            style={[styles.goButton, isOnline ? styles.stopBtn : styles.goBtn]}
            onPress={() => setIsOnline((prev) => !prev)}
          >
            <Text style={styles.goText}>{isOnline ? "STOP" : "GO"}</Text>
          </TouchableOpacity>

          {/* Schedule button */}
          <TouchableOpacity style={styles.scheduleButton} onPress={() => setIsScheduleOpen(true)}>
            <Ionicons name="calendar-outline" size={22} color="#000" />
            <Text style={styles.scheduleText}>Schedule</Text>
          </TouchableOpacity>

          {/* Status banner */}
          <DriverStatus isOnline={isOnline} drivingSeconds={drivingSeconds} />
        </View>
      )}

      {/* Schedule panel */}
      <SchedulePanel visible={isScheduleOpen} onClose={() => setIsScheduleOpen(false)} />

      {/* 🚨 Wellness Nudge */}
      <WellnessNudge
        drivingSeconds={drivingSeconds}
        onOpenCopilot={() => navigation.navigate("Copilot")}
      />
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
  goButton: {
    width: 100,
    height: 100,
    borderRadius: 50,
    justifyContent: "center",
    alignItems: "center",
    elevation: 5,
    marginBottom: 20,
  },
  goBtn: { backgroundColor: "#007AFF" },
  stopBtn: { backgroundColor: "#E11900" },
  goText: {
    color: "#fff",
    fontSize: 24,
    fontWeight: "bold",
  },
  scheduleButton: {
    flexDirection: "row",
    backgroundColor: "#fff",
    borderRadius: 25,
    paddingVertical: 10,
    paddingHorizontal: 20,
    alignItems: "center",
    marginBottom: 10,
    shadowColor: "#000",
    shadowOpacity: 0.1,
    shadowOffset: { width: 0, height: 2 },
    shadowRadius: 4,
    elevation: 3,
  },
  scheduleText: {
    marginLeft: 6,
    fontSize: 16,
    fontWeight: "500",
  },
});
