import { NavigationContainer } from "@react-navigation/native";
import { createNativeStackNavigator } from "@react-navigation/native-stack";
import { StatusBar } from "expo-status-bar";
import React from "react";

import MapHomeScreen from "./screens/MapHomeScreen";
import MapZoneScreen from "./screens/MapZoneScreen";
import RecommendationsScreen from "./screens/RecommendationsScreen";
import ScheduleScreen from "./screens/ScheduleScreen";
import AIChatScreen from "./screens/AIChatScreen";

const Stack = createNativeStackNavigator();

export default function App() {
  return (
    <NavigationContainer>
      <Stack.Navigator screenOptions={{ headerShown: false }}>
        <Stack.Screen name="MapHome" component={MapHomeScreen} />
        <Stack.Screen name="Schedule" component={ScheduleScreen} />
        <Stack.Screen name="Recommendations" component={RecommendationsScreen} />
        <Stack.Screen name="MapZone" component={MapZoneScreen} />
        <Stack.Screen name="AIChat" component={AIChatScreen} />
      </Stack.Navigator>

      <StatusBar style="auto" />
    </NavigationContainer>
  );
}
