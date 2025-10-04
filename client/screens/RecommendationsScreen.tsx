import { useNavigation } from "@react-navigation/native";
import React from "react";
import { ScrollView, StyleSheet, Text, TouchableOpacity } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

const MOCK_RECOMMENDATIONS = [
  { id: 1, zone: "Downtown", time: "Now", distance: "2.1 km" },
  { id: 2, zone: "Airport Area", time: "In 1 hour", distance: "12.4 km" },
  { id: 3, zone: "University District", time: "Tomorrow 7 AM", distance: "5.6 km" },
];

export default function RecommendationsScreen({ route }: any) {
  const navigation = useNavigation<any>();

  return (
    <SafeAreaView style={styles.container}>
      <Text style={styles.title}>Recommended Driving Zones</Text>
      <ScrollView>
        {MOCK_RECOMMENDATIONS.map((r) => (
          <TouchableOpacity
            key={r.id}
            style={styles.card}
            onPress={() => navigation.navigate("MapZone", { zone: r })}
          >
            <Text style={styles.zone}>{r.zone}</Text>
            <Text style={styles.time}>{r.time}</Text>
            <Text style={styles.distance}>{r.distance} away</Text>
          </TouchableOpacity>
        ))}
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#fff", padding: 20 },
  title: { fontSize: 22, fontWeight: "bold", marginBottom: 16 },
  card: {
    backgroundColor: "#f8f8f8",
    padding: 16,
    borderRadius: 10,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: "#e0e0e0",
  },
  zone: { fontSize: 18, fontWeight: "600" },
  time: { color: "#555", marginTop: 4 },
  distance: { color: "#777", marginTop: 2 },
});
