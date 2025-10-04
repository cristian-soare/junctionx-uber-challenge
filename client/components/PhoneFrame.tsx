import React from "react";
import { Platform, StyleSheet, View } from "react-native";

export default function PhoneFrame({ children }: { children: React.ReactNode }) {
  const isWeb = Platform.OS === "web";

  return (
    <View style={styles.screenContainer}>
      <View style={[styles.phoneFrame, { height: isWeb ? "90%" : "100%" }]}>
        {children}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  screenContainer: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: "#f7f7f7",
  },
  phoneFrame: {
    width: 384,
    borderRadius: 36,
    overflow: "hidden",
    borderWidth: 8,
    borderColor: "#000",
    backgroundColor: "#000",
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.3,
    shadowRadius: 12,
    elevation: 10,
  },
});
