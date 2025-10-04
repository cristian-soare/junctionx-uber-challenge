import { useNavigation } from "@react-navigation/native";
import React, { useState } from "react";
import { StyleSheet, Text, TextInput, TouchableOpacity } from "react-native";
import DateTimePickerModal from "react-native-modal-datetime-picker";
import { SafeAreaView } from "react-native-safe-area-context";

export default function ScheduleScreen() {
  const navigation = useNavigation<any>();
  const [isDatePickerVisible, setDatePickerVisibility] = useState(false);
  const [startTime, setStartTime] = useState<Date | null>(null);
  const [hours, setHours] = useState("");

  const confirmDate = (date: Date) => {
    setStartTime(date);
    setDatePickerVisibility(false);
  };

  return (
    <SafeAreaView style={styles.container}>
      <Text style={styles.title}>Schedule your drive</Text>

      <TouchableOpacity onPress={() => setDatePickerVisibility(true)} style={styles.inputBox}>
        <Text>{startTime ? startTime.toLocaleTimeString() : "Select start time"}</Text>
      </TouchableOpacity>

      <DateTimePickerModal
        isVisible={isDatePickerVisible}
        mode="time"
        onConfirm={confirmDate}
        onCancel={() => setDatePickerVisibility(false)}
      />

      <TextInput
        style={styles.input}
        placeholder="Enter driving hours (e.g. 4)"
        keyboardType="numeric"
        value={hours}
        onChangeText={setHours}
      />

      <TouchableOpacity
        style={styles.continueButton}
        onPress={() =>
          navigation.navigate("Recommendations", {
            schedule: { startTime, hours },
          })
        }
      >
        <Text style={styles.continueText}>Get Recommendations</Text>
      </TouchableOpacity>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, padding: 20, backgroundColor: "#fff" },
  title: { fontSize: 22, fontWeight: "bold", marginBottom: 24 },
  inputBox: {
    padding: 14,
    borderColor: "#ddd",
    borderWidth: 1,
    borderRadius: 8,
    marginBottom: 20,
  },
  input: {
    borderWidth: 1,
    borderColor: "#ddd",
    borderRadius: 8,
    padding: 14,
    marginBottom: 20,
  },
  continueButton: {
    backgroundColor: "#000",
    padding: 16,
    borderRadius: 10,
    alignItems: "center",
  },
  continueText: { color: "#fff", fontWeight: "bold", fontSize: 16 },
});
