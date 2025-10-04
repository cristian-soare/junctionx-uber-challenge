import { Ionicons } from "@expo/vector-icons";
import { useNavigation } from "@react-navigation/native";
import * as Location from "expo-location";
import React, { useEffect, useState } from "react";
import { StyleSheet, Text, TouchableOpacity, View } from "react-native";
import MapView, { Marker, Region } from "react-native-maps";
import { SafeAreaView } from "react-native-safe-area-context";

export default function MapHomeScreen() {
  const navigation = useNavigation<any>();
  const [location, setLocation] = useState<Region | null>(null);

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

  if (!location)
    return (
      <View style={styles.loading}>
        <Text>Loading map...</Text>
      </View>
    );

  return (
    <SafeAreaView style={styles.container}>
      <MapView style={StyleSheet.absoluteFillObject} region={location}>
        <Marker coordinate={location} title="You" pinColor="blue" />
      </MapView>

      {/* Bottom buttons */}
      <View style={styles.bottomContainer}>
        <TouchableOpacity style={styles.goButton}>
          <Text style={styles.goText}>GO</Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={styles.scheduleButton}
          onPress={() => navigation.navigate("Schedule")}
        >
          <Ionicons name="calendar-outline" size={22} color="#000" />
          <Text style={styles.scheduleText}>Schedule</Text>
        </TouchableOpacity>
      </View>
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
  bottomContainer: {
    position: "absolute",
    bottom: 60,
    width: "100%",
    alignItems: "center",
  },
  goButton: {
    backgroundColor: "#007AFF",
    width: 100,
    height: 100,
    borderRadius: 50,
    justifyContent: "center",
    alignItems: "center",
    elevation: 4,
  },
  goText: { color: "#fff", fontSize: 24, fontWeight: "bold" },
  scheduleButton: {
    flexDirection: "row",
    backgroundColor: "#fff",
    borderRadius: 25,
    paddingVertical: 10,
    paddingHorizontal: 20,
    marginTop: 20,
    alignItems: "center",
  },
  scheduleText: { marginLeft: 6, fontSize: 16, fontWeight: "500" },
});
