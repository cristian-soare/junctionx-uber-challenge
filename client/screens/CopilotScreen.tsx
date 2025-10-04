import { useNavigation } from "@react-navigation/native";
import React from "react";
import { StyleSheet, Text, TouchableOpacity, View } from "react-native";
import PhoneFrame from "../components/PhoneFrame";

export default function CopilotScreen() {
  const navigation = useNavigation<any>();

  return (
    <PhoneFrame>
      <View style={styles.container}>
        <Text style={styles.title}>AI Copilot</Text>
        <Text style={styles.subtitle}>
          Personalized insights, predictive ride suggestions, and well-being tips.
        </Text>
        <TouchableOpacity
          style={styles.backButton}
          onPress={() => navigation.navigate("Main")}
        >
          <Text style={styles.backText}>← Back</Text>
        </TouchableOpacity>
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
    fontSize: 28,
    fontWeight: "bold",
    marginBottom: 12,
  },
  subtitle: {
    fontSize: 16,
    textAlign: "center",
    color: "#444",
    marginBottom: 24,
  },
  backButton: {
    backgroundColor: "#000",
    paddingHorizontal: 20,
    paddingVertical: 10,
    borderRadius: 8,
  },
  backText: {
    color: "#fff",
    fontSize: 16,
  },
});
