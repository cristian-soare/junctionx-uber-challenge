import React from "react";
import { StyleSheet } from "react-native";
import MapView, { Circle, Marker } from "react-native-maps";
import { SafeAreaView } from "react-native-safe-area-context";

export default function MapZoneScreen({ route }: any) {
  const { zone } = route.params;

  // Mock coordinates (in real app, backend sends these)
  const mockZone = {
    latitude: 37.7749,
    longitude: -122.4194,
  };

  return (
    <SafeAreaView style={styles.container}>
      <MapView
        style={StyleSheet.absoluteFillObject}
        initialRegion={{
          ...mockZone,
          latitudeDelta: 0.05,
          longitudeDelta: 0.05,
        }}
      >
        <Marker coordinate={mockZone} title={zone.zone} />
        <Circle
          center={mockZone}
          radius={2000}
          strokeColor="rgba(0, 150, 255, 0.5)"
          fillColor="rgba(0, 150, 255, 0.2)"
        />
      </MapView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
});
