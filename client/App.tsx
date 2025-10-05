import { NavigationContainer } from "@react-navigation/native";
import { createNativeStackNavigator } from "@react-navigation/native-stack";
import { StatusBar } from "expo-status-bar";
import React, { useEffect, useState } from "react";
import { View, Text, ActivityIndicator } from "react-native";

import AIChatScreen from "./screens/AIChatScreen";
import CopilotScreen from "./screens/CopilotScreen";
import MapHomeScreen from "./screens/MapHomeScreen";
import WellbeingScreen from "./screens/WellbeingScreen";
import { getOrCreateDriverId } from "./services/driverService";
import Config from "./config/Config";

const Stack = createNativeStackNavigator();

export default function App() {
  const [isReady, setIsReady] = useState(false);

  useEffect(() => {
    const initializeDriver = async () => {
      try {
        const driverId = await getOrCreateDriverId();
        Config.DRIVER_ID = driverId;
        console.log("Driver initialized:", driverId);
      } catch (error) {
        console.error("Failed to initialize driver:", error);
      } finally {
        setIsReady(true);
      }
    };

    initializeDriver();
  }, []);

  if (!isReady) {
    return (
      <View style={{ flex: 1, justifyContent: "center", alignItems: "center" }}>
        <ActivityIndicator size="large" color="#000" />
        <Text style={{ marginTop: 10 }}>Initializing...</Text>
      </View>
    );
  }

  return (
    <NavigationContainer>
      <Stack.Navigator
        screenOptions={{
          headerShown: false,
          animation: "slide_from_right",
        }}
      >
        {/* 🏠 Main app entry (you can later choose which is default) */}
        <Stack.Screen name="Main" component={MapHomeScreen} />

        {/* 🗺️ Map / Driver Home
        <Stack.Screen name="MapHome" component={MapHomeScreen} /> */}

        {/* 🤖 AI Copilot Chat */}
        <Stack.Screen name="Copilot" component={CopilotScreen} />

        {/* 💆‍♂️ Wellbeing page (if you keep it) */}
        <Stack.Screen name="Wellbeing" component={WellbeingScreen} />
        <Stack.Screen name="AIChat" component={AIChatScreen} />
      </Stack.Navigator>

      <StatusBar style="auto" />
    </NavigationContainer>
  );
}
