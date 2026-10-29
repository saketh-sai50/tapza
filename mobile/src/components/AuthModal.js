import React, { useState } from "react";
import {
  Modal,
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  ActivityIndicator,
  Alert
} from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { useApp } from "../context/AppContext";

export const AuthModal = ({ visible, onClose }) => {
  const { login } = useApp();
  const [role, setRole] = useState("CUSTOMER");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const handleLogin = async () => {
    if (!email.trim() || !password.trim()) {
      Alert.alert("Missing Fields", "Please enter your username/email and password.");
      return;
    }

    setIsLoading(true);
    try {
      await login(email.trim(), password.trim(), role);
      Alert.alert("Success", `Logged in as ${role === "PHARMACY" ? "Pharmacy Partner" : "Customer"}!`);
      onClose();
    } catch (e) {
      Alert.alert("Login Failed", e.message || "Invalid credentials.");
    } finally {
      setIsLoading(false);
    }
  };

  const fillQuickDemo = (demoUser, demoPass, demoRole) => {
    setEmail(demoUser);
    setPassword(demoPass);
    setRole(demoRole);
  };

  return (
    <Modal visible={visible} transparent animationType="slide" onRequestClose={onClose}>
      <View style={styles.overlay}>
        <View style={styles.card}>
          {/* Header */}
          <View style={styles.header}>
            <Text style={styles.title}>Account Access</Text>
            <TouchableOpacity style={styles.closeBtn} onPress={onClose}>
              <Ionicons name="close" size={20} color="#64748b" />
            </TouchableOpacity>
          </View>

          {/* Role Tabs */}
          <View style={styles.roleTabs}>
            <TouchableOpacity
              style={[styles.roleTab, role === "CUSTOMER" && styles.roleTabActive]}
              onPress={() => setRole("CUSTOMER")}
            >
              <Ionicons
                name="person"
                size={14}
                color={role === "CUSTOMER" ? "#16a34a" : "#64748b"}
              />
              <Text
                style={[styles.roleTabText, role === "CUSTOMER" && styles.roleTabTextActive]}
              >
                Customer
              </Text>
            </TouchableOpacity>

            <TouchableOpacity
              style={[styles.roleTab, role === "PHARMACY" && styles.roleTabActive]}
              onPress={() => setRole("PHARMACY")}
            >
              <Ionicons
                name="medical"
                size={14}
                color={role === "PHARMACY" ? "#16a34a" : "#64748b"}
              />
              <Text
                style={[styles.roleTabText, role === "PHARMACY" && styles.roleTabTextActive]}
              >
                Pharmacy Partner
              </Text>
            </TouchableOpacity>
          </View>

          {/* Inputs */}
          <View style={styles.inputsGroup}>
            <View style={styles.inputWrap}>
              <Text style={styles.inputLabel}>
                {role === "PHARMACY" ? "Pharmacy Username / Email" : "Phone or Email"}
              </Text>
              <TextInput
                style={styles.input}
                placeholder={role === "PHARMACY" ? "testpharm001" : "saketh@tapza.com"}
                placeholderTextColor="#94a3b8"
                value={email}
                onChangeText={setEmail}
                autoCapitalize="none"
              />
            </View>

            <View style={styles.inputWrap}>
              <Text style={styles.inputLabel}>Password</Text>
              <TextInput
                style={styles.input}
                placeholder="Enter password..."
                placeholderTextColor="#94a3b8"
                secureTextEntry
                value={password}
                onChangeText={setPassword}
              />
            </View>
          </View>

          {/* Quick Demo Fill Buttons */}
          <View style={styles.demoSection}>
            <Text style={styles.demoLabel}>1-Tap Demo Credentials:</Text>
            <View style={styles.demoRow}>
              <TouchableOpacity
                style={styles.demoBtn}
                onPress={() => fillQuickDemo("customer_demo", "customer@123", "CUSTOMER")}
              >
                <Text style={styles.demoBtnText}>Customer</Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={styles.demoBtn}
                onPress={() => fillQuickDemo("testpharm001", "testpharm@001", "PHARMACY")}
              >
                <Text style={styles.demoBtnText}>Pharmacy 1</Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={styles.demoBtn}
                onPress={() => fillQuickDemo("testpharm002", "testpharm@002", "PHARMACY")}
              >
                <Text style={styles.demoBtnText}>Pharmacy 2</Text>
              </TouchableOpacity>
            </View>
          </View>

          {/* Submit */}
          <TouchableOpacity
            style={styles.submitBtn}
            activeOpacity={0.85}
            disabled={isLoading}
            onPress={handleLogin}
          >
            {isLoading ? (
              <ActivityIndicator color="#fff" />
            ) : (
              <Text style={styles.submitBtnText}>
                Log In as {role === "PHARMACY" ? "Pharmacy" : "Customer"}
              </Text>
            )}
          </TouchableOpacity>
        </View>
      </View>
    </Modal>
  );
};

const styles = StyleSheet.create({
  overlay: {
    flex: 1,
    backgroundColor: "rgba(0, 0, 0, 0.55)",
    justifyContent: "flex-end"
  },
  card: {
    backgroundColor: "#ffffff",
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    padding: 20,
    paddingBottom: 30
  },
  header: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 16
  },
  title: {
    fontSize: 17,
    fontWeight: "900",
    color: "#0f172a"
  },
  closeBtn: {
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: "#f1f5f9",
    alignItems: "center",
    justifyContent: "center"
  },
  roleTabs: {
    flexDirection: "row",
    backgroundColor: "#f1f5f9",
    borderRadius: 10,
    padding: 4,
    marginBottom: 16
  },
  roleTab: {
    flex: 1,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    paddingVertical: 8,
    borderRadius: 8,
    gap: 6
  },
  roleTabActive: {
    backgroundColor: "#ffffff",
    shadowColor: "#000",
    shadowOpacity: 0.05,
    shadowRadius: 2,
    elevation: 2
  },
  roleTabText: {
    fontSize: 12.5,
    fontWeight: "700",
    color: "#64748b"
  },
  roleTabTextActive: {
    color: "#166534",
    fontWeight: "800"
  },
  inputsGroup: {
    gap: 12,
    marginBottom: 16
  },
  inputWrap: {},
  inputLabel: {
    fontSize: 11.5,
    fontWeight: "700",
    color: "#334155",
    marginBottom: 4
  },
  input: {
    backgroundColor: "#f8fafc",
    borderWidth: 1,
    borderColor: "#cbd5e1",
    borderRadius: 8,
    paddingHorizontal: 12,
    paddingVertical: 10,
    fontSize: 13,
    color: "#0f172a"
  },
  demoSection: {
    marginBottom: 16,
    padding: 10,
    backgroundColor: "#f8fafc",
    borderRadius: 8,
    borderWidth: 1,
    borderColor: "#e2e8f0"
  },
  demoLabel: {
    fontSize: 10.5,
    fontWeight: "800",
    color: "#64748b",
    marginBottom: 6,
    textTransform: "uppercase"
  },
  demoRow: {
    flexDirection: "row",
    gap: 8
  },
  demoBtn: {
    flex: 1,
    backgroundColor: "#ffffff",
    borderWidth: 1,
    borderColor: "#cbd5e1",
    paddingVertical: 6,
    borderRadius: 6,
    alignItems: "center"
  },
  demoBtnText: {
    fontSize: 11.5,
    fontWeight: "700",
    color: "#0f172a"
  },
  submitBtn: {
    backgroundColor: "#16a34a",
    paddingVertical: 12,
    borderRadius: 10,
    alignItems: "center"
  },
  submitBtnText: {
    color: "#ffffff",
    fontSize: 13.5,
    fontWeight: "900"
  }
});
