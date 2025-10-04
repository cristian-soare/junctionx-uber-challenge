import { NavigationContainer } from "@react-navigation/native";
import { createNativeStackNavigator } from "@react-navigation/native-stack";
import { StatusBar } from "expo-status-bar";
import React from "react";

import AIChatScreen from "./screens/AIChatScreen";
import CopilotScreen from "./screens/CopilotScreen";
import MapHomeScreen from "./screens/MapHomeScreen";
import WellbeingScreen from "./screens/WellbeingScreen";

const Stack = createNativeStackNavigator();

export default function App() {
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
