import { NavigationContainer } from "@react-navigation/native";
import { createNativeStackNavigator } from "@react-navigation/native-stack";
import { StatusBar } from "expo-status-bar";
import React from "react";

import CopilotScreen from "./screens/CopilotScreen";
import MainScreen from "./screens/MainScreen";
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
        <Stack.Screen name="Main" component={MainScreen} />
        <Stack.Screen name="Copilot" component={CopilotScreen} />
        <Stack.Screen name="Wellbeing" component={WellbeingScreen} />
      </Stack.Navigator>
      <StatusBar style="auto" />
    </NavigationContainer>
  );
}
