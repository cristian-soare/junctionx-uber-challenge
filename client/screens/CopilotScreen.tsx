import { Ionicons } from "@expo/vector-icons";
import { useNavigation } from "@react-navigation/native";
import React, { useState } from "react";
import {
  ActivityIndicator,
  Alert,
  FlatList,
  KeyboardAvoidingView,
  Platform,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import Config from "../config/Config";
import { sendChatMessage } from "../services/aiService";

export default function CopilotScreen() {
  const navigation = useNavigation<any>();

  const [messages, setMessages] = useState([
    { role: "model", content: "👋 Hey driver! How can I help you today?" },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSend = async () => {
    if (!input.trim()) return;
    const userMessage = { role: "user", content: input };
    setMessages((prev) => [...prev, userMessage]);
    const currentInput = input;
    setInput("");
    setLoading(true);

    try {
      // Prepare chat history for the API (exclude the message we just added)
      const chatHistory = messages.map((msg) => ({
        role: (msg.role === "model" ? "assistant" : "user") as "user" | "assistant",
        content: msg.content,
      }));

      // Call the AI chat endpoint via service
      const data = await sendChatMessage(
        Config.DEFAULT_DRIVER_ID,
        currentInput,
        chatHistory
      );

      // Add AI response to messages
      setMessages((prev) => [
        ...prev,
        { role: "model", content: data.response },
      ]);
    } catch (e) {
      console.error("Chat error:", e);

      // Show error message to user
      Alert.alert(
        "Connection Error",
        "Unable to reach AI assistant. Please check your connection and try again."
      );

      // Add error message to chat
      setMessages((prev) => [
        ...prev,
        {
          role: "model",
          content:
            "Sorry, I'm having trouble connecting right now. Please try again in a moment.",
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <SafeAreaView style={styles.safeArea}>
      <KeyboardAvoidingView
        style={styles.container}
        behavior={Platform.OS === "ios" ? "padding" : undefined}
      >
        {/* Header */}
        <View style={styles.header}>
          <TouchableOpacity onPress={() => navigation.navigate("Main")}>
            <Ionicons name="arrow-back" size={24} color="#000" />
          </TouchableOpacity>
          <Text style={styles.headerText}>AI Copilot</Text>
          <View style={{ width: 24 }} />
        </View>

        {/* Messages */}
        <FlatList
          data={messages}
          keyExtractor={(_, i) => i.toString()}
          renderItem={({ item }) => (
            <View
              style={[
                styles.messageBubble,
                item.role === "user" ? styles.userBubble : styles.aiBubble,
              ]}
            >
              <Text
                style={{
                  color: item.role === "user" ? "#fff" : "#000",
                }}
              >
                {item.content}
              </Text>
            </View>
          )}
          contentContainerStyle={styles.chatContainer}
        />

        {loading && <ActivityIndicator size="small" color="#007AFF" />}

        {/* Input bar */}
        <View style={styles.inputContainer}>
          <TextInput
            style={styles.input}
            value={input}
            placeholder="Ask your copilot..."
            onChangeText={setInput}
          />
          <TouchableOpacity style={styles.sendButton} onPress={handleSend}>
            <Ionicons name="send" size={20} color="#fff" />
          </TouchableOpacity>
        </View>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: { flex: 1, backgroundColor: "#fff" },
  container: { flex: 1, padding: 16 },
  header: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    marginBottom: 10,
  },
  headerText: { fontSize: 18, fontWeight: "bold" },
  chatContainer: { flexGrow: 1, paddingVertical: 10 },
  messageBubble: {
    padding: 12,
    borderRadius: 16,
    marginVertical: 6,
    maxWidth: "80%",
  },
  userBubble: {
    backgroundColor: "#007AFF",
    alignSelf: "flex-end",
  },
  aiBubble: {
    backgroundColor: "#F2F2F2",
    alignSelf: "flex-start",
  },
  inputContainer: {
    flexDirection: "row",
    alignItems: "center",
    backgroundColor: "#F2F2F2",
    borderRadius: 25,
    paddingHorizontal: 10,
    marginTop: 10,
  },
  input: {
    flex: 1,
    paddingHorizontal: 10,
    height: 45,
  },
  sendButton: {
    backgroundColor: "#007AFF",
    borderRadius: 20,
    padding: 10,
  },
});
