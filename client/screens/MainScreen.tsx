import { useNavigation } from "@react-navigation/native";
import React, { useEffect, useState } from "react";
import {
  ImageBackground,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from "react-native";
import CopilotAlert from "../components/CopilotAlert";
import PhoneFrame from "../components/PhoneFrame";

export default function MainScreen() {
  const navigation = useNavigation<any>();
  const [alertType, setAlertType] = useState<"ok" | "warning" | "danger" | null>(null);
  const [alertVisible, setAlertVisible] = useState(false);

  // 👇 Auto-cycle alerts every 3 seconds
  useEffect(() => {
    const types: ("ok" | "warning" | "danger")[] = ["ok", "warning", "danger"];
    let i = 0;

    const interval = setInterval(() => {
      setAlertType(types[i]);
      setAlertVisible(true); // make sure alert shows each time
      i = (i + 1) % types.length;
    }, 3000);

    return () => clearInterval(interval);
  }, []);

  return (
    <PhoneFrame>
      <ImageBackground
        source={require("../assets/uber-background.png")}
        style={styles.fullBackground}
        imageStyle={styles.imageStyle}
        resizeMode="cover"
      >
        <View style={styles.overlay}>
          <View style={styles.copilotWrapper}>
            <TouchableOpacity
              style={styles.copilotButton}
              onPress={() => navigation.navigate("Copilot")}
            >
              <Text style={styles.copilotText}>🤖</Text>
            </TouchableOpacity>

            {/* Copilot alert bubble */}
            <View style={styles.alertContainer}>
              <CopilotAlert
                type={alertType || "ok"}
                visible={alertVisible}
                onHide={() => setAlertVisible(false)} // reset visibility when fade-out completes
                message={
                  alertType === "ok"
                    ? "✅ You're good to go — all systems look great!"
                    : alertType === "warning"
                    ? "⚠️ Consider a short break — you’ve been active for a while."
                    : "🚨 You’ve been driving for a long stretch — please rest soon."
                }
              />
            </View>
          </View>
        </View>
      </ImageBackground>
    </PhoneFrame>
  );
}

const styles = StyleSheet.create({
  fullBackground: {
    flex: 1,
    width: "100%",
    height: "100%",
    justifyContent: "flex-start",
    alignItems: "center",
  },
  imageStyle: {
    width: "100%",
    height: "100%",
    borderRadius: 36,
  },
  overlay: {
    flex: 1,
    width: "100%",
    justifyContent: "flex-start",
    alignItems: "center",
    paddingTop: 40,
  },
  copilotWrapper: {
    width: "90%",
    alignItems: "flex-end",
    position: "relative",
  },
  copilotButton: {
    backgroundColor: "#000",
    width: 60,
    height: 60,
    borderRadius: 30,
    alignItems: "center",
    justifyContent: "center",
    opacity: 0.9,
  },
  copilotText: {
    color: "#fff",
    fontSize: 24,
  },
  alertContainer: {
    position: "absolute",
    top: 70,
    right: 0,
    width: "100%",
  },
});
