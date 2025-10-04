import { useNavigation } from "@react-navigation/native";
import React, { useEffect, useState } from "react";
import {
  ImageBackground,
  Platform,
  StatusBar,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import CopilotAlert from "../components/CopilotAlert";

export default function MainScreen() {
  const navigation = useNavigation<any>();
  const [alertType, setAlertType] = useState<"ok" | "warning" | "danger" | null>(null);
  const [alertVisible, setAlertVisible] = useState(false);

  // cycle alerts
  useEffect(() => {
    const types: ("ok" | "warning" | "danger")[] = ["ok", "warning", "danger"];
    let i = 0;
    const interval = setInterval(() => {
      setAlertType(types[i]);
      setAlertVisible(true);
      i = (i + 1) % types.length;
    }, 3000);
    return () => clearInterval(interval);
  }, []);

  return (
    <SafeAreaView style={styles.safeArea} edges={["top", "left", "right"]}>
      {/* ✅ Make sure status bar is translucent & overlays image */}
      <StatusBar translucent backgroundColor="transparent" barStyle="light-content" />

      <ImageBackground
        source={require("../assets/uber-background.png")}
        style={styles.background}
        imageStyle={styles.imageStyle}
        resizeMode="cover"
      >
        <View style={styles.overlay}>
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
              onHide={() => setAlertVisible(false)}
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
      </ImageBackground>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: "#000", // fallback while image loads
  },
  background: {
    flex: 1,
    justifyContent: "flex-start",
  },
  imageStyle: {
    width: "100%",
    height: "100%",
  },
  overlay: {
    flex: 1,
    justifyContent: "flex-start",
    alignItems: "flex-end",
    paddingTop: Platform.OS === "android" ? 40 : 0, // Android needs this offset
    paddingRight: 20,
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
    top: 100,
    alignSelf: "center",
    width: "90%",
  },
});
