// components/CopilotAlert.tsx
import React, { useEffect, useRef } from "react";
import { Animated, StyleSheet, Text, ViewStyle } from "react-native";

interface CopilotAlertProps {
  type: "ok" | "warning" | "danger";
  message: string;
  visible: boolean;
  onHide?: () => void;
}

export default function CopilotAlert({
  type,
  message,
  visible,
  onHide,
}: CopilotAlertProps) {
  const fadeAnim = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    if (visible) {
      Animated.timing(fadeAnim, {
        toValue: 1,
        duration: 300,
        useNativeDriver: true,
      }).start();

      const timer = setTimeout(() => {
        Animated.timing(fadeAnim, {
          toValue: 0,
          duration: 300,
          useNativeDriver: true,
        }).start(() => onHide && onHide());
      }, 4000);

      return () => clearTimeout(timer);
    }
  }, [visible]);

  if (!visible) return null;

  const backgroundColors: Record<string, string> = {
    ok: "#00B26F", // green - all good
    warning: "#F5A623", // yellow/orange - mild caution
    danger: "#E11900", // red - critical
  };

  const containerStyle: ViewStyle = {
    backgroundColor: backgroundColors[type],
  };

  return (
    <Animated.View
      style={[
        styles.alertBubble,
        containerStyle,
        { opacity: fadeAnim, transform: [{ translateY: fadeAnim.interpolate({
          inputRange: [0, 1],
          outputRange: [-10, 0],
        }) }] },
      ]}
    >
      <Text style={styles.alertText}>{message}</Text>
    </Animated.View>
  );
}

const styles = StyleSheet.create({
  alertBubble: {
    borderRadius: 16,
    paddingHorizontal: 20,
    paddingVertical: 14,
    width: "100%",
    shadowColor: "#000",
    shadowOpacity: 0.25,
    shadowOffset: { width: 0, height: 4 },
    shadowRadius: 8,
    elevation: 5,
  },
  alertText: {
    color: "#fff",
    fontSize: 16,
    fontWeight: "600",
    textAlign: "center",
  },
});
