import React from "react";
import { StyleSheet, Text, View } from "react-native";
import PhoneFrame from "../components/PhoneFrame";

export default function WellbeingScreen() {
  return (
    <PhoneFrame>
      <View style={styles.container}>
        <Text style={styles.title}>Driver Well-being</Text>
        <Text style={styles.text}>
          Break reminders, optimal routes, and energy-saving tips will appear here.
        </Text>
      </View>
    </PhoneFrame>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: "center",
    alignItems: "center",
    padding: 24,
    backgroundColor: "#fff",
  },
  title: {
    fontSize: 26,
    fontWeight: "bold",
    marginBottom: 12,
  },
  text: {
    fontSize: 16,
    color: "#444",
    textAlign: "center",
  },
});
