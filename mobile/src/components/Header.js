import React, { useState } from "react";
import {
  View,
  Text,
  TouchableOpacity,
  Modal,
  StyleSheet,
  SafeAreaView
} from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { useApp } from "../context/AppContext";

export const Header = ({ onOpenAuth }) => {
  const { user, zone, updateZone } = useApp();
  const [showLocationModal, setShowLocationModal] = useState(false);

  const zones = ["Warangal", "Hanamkonda", "Kazipet"];

  return (
    <SafeAreaView style={styles.safeArea}>
      <View style={styles.container}>
        {/* Logo */}
        <View style={styles.logoContainer}>
          <Text style={styles.logoText}>
            Tapza<Text style={styles.logoDot}>•</Text>
          </Text>
        </View>

        {/* Location Pill */}
        <TouchableOpacity
          style={styles.locationPill}
          activeOpacity={0.8}
          onPress={() => setShowLocationModal(true)}
        >
          <View style={styles.locationIconCircle}>
            <Ionicons name="location-sharp" size={13} color="#fff" />
          </View>
          <View style={styles.locationTextWrap}>
            <View style={styles.locationRow}>
              <Text style={styles.locationZone}>{zone.toUpperCase()}</Text>
              <Ionicons name="chevron-down" size={12} color="#fff" />
            </View>
            <Text style={styles.locationSub} numberOfLines={1}>
              Fast Delivery Area, {zone}
            </Text>
          </View>
        </TouchableOpacity>

        {/* User / Bell Pill */}
        <View style={styles.rightActions}>
          <TouchableOpacity style={styles.iconBtn}>
            <Ionicons name="notifications-outline" size={18} color="#fff" />
          </TouchableOpacity>
          <TouchableOpacity
            style={styles.userBtn}
            activeOpacity={0.8}
            onPress={onOpenAuth}
          >
            <View style={styles.avatar}>
              <Text style={styles.avatarText}>
                {user?.full_name ? user.full_name[0].toUpperCase() : "G"}
              </Text>
            </View>
            <View style={styles.userTextWrap}>
              <Text style={styles.welcomeText}>Welcome</Text>
              <Text style={styles.userNameText} numberOfLines={1}>
                {user ? `Hi, ${user.full_name.split(" ")[0]} 👋` : "Log in"}
              </Text>
            </View>
          </TouchableOpacity>
        </View>
      </View>

      {/* Location Picker Modal */}
      <Modal
        visible={showLocationModal}
        transparent
        animationType="fade"
        onRequestClose={() => setShowLocationModal(false)}
      >
        <TouchableOpacity
          style={styles.modalOverlay}
          activeOpacity={1}
          onPress={() => setShowLocationModal(false)}
        >
          <View style={styles.modalCard} onStartShouldSetResponder={() => true}>
            <View style={styles.modalHeader}>
              <Text style={styles.modalTitle}>Choose Delivery Zone</Text>
              <TouchableOpacity onPress={() => setShowLocationModal(false)}>
                <Ionicons name="close" size={20} color="#64748b" />
              </TouchableOpacity>
            </View>
            <Text style={styles.modalSubtitle}>
              Orders will be broadcasted to licensed pharmacies within this zone:
            </Text>

            {zones.map((z) => {
              const isSelected = zone.toLowerCase() === z.toLowerCase();
              return (
                <TouchableOpacity
                  key={z}
                  style={[
                    styles.zoneOption,
                    isSelected && styles.zoneOptionActive
                  ]}
                  onPress={() => {
                    updateZone(z);
                    setShowLocationModal(false);
                  }}
                >
                  <View style={styles.zoneRow}>
                    <Ionicons
                      name="location"
                      size={18}
                      color={isSelected ? "#16a34a" : "#64748b"}
                    />
                    <Text
                      style={[
                        styles.zoneName,
                        isSelected && styles.zoneNameActive
                      ]}
                    >
                      {z}
                    </Text>
                  </View>
                  {isSelected && (
                    <Ionicons name="checkmark-circle" size={20} color="#16a34a" />
                  )}
                </TouchableOpacity>
              );
            })}
          </View>
        </TouchableOpacity>
      </Modal>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  safeArea: {
    backgroundColor: "#1e1b4b"
  },
  container: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    paddingHorizontal: 14,
    paddingVertical: 10,
    backgroundColor: "#1e1b4b"
  },
  logoContainer: {
    flexShrink: 0
  },
  logoText: {
    color: "#ffffff",
    fontSize: 22,
    fontWeight: "900",
    letterSpacing: -0.5
  },
  logoDot: {
    color: "#10b981"
  },
  locationPill: {
    flexDirection: "row",
    alignItems: "center",
    backgroundColor: "rgba(255, 255, 255, 0.12)",
    paddingVertical: 4,
    paddingHorizontal: 8,
    borderRadius: 20,
    maxWidth: 160
  },
  locationIconCircle: {
    width: 22,
    height: 22,
    borderRadius: 11,
    backgroundColor: "rgba(255, 255, 255, 0.2)",
    alignItems: "center",
    justifyContent: "center",
    marginRight: 6
  },
  locationTextWrap: {
    flex: 1
  },
  locationRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 2
  },
  locationZone: {
    color: "#ffffff",
    fontSize: 11,
    fontWeight: "800",
    letterSpacing: 0.3
  },
  locationSub: {
    color: "#cbd5e1",
    fontSize: 9.5,
    fontWeight: "500"
  },
  rightActions: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8
  },
  iconBtn: {
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: "rgba(255, 255, 255, 0.15)",
    alignItems: "center",
    justifyContent: "center"
  },
  userBtn: {
    flexDirection: "row",
    alignItems: "center",
    gap: 6
  },
  avatar: {
    width: 28,
    height: 28,
    borderRadius: 14,
    backgroundColor: "rgba(255, 255, 255, 0.25)",
    alignItems: "center",
    justifyContent: "center"
  },
  avatarText: {
    color: "#fff",
    fontSize: 13,
    fontWeight: "800"
  },
  userTextWrap: {
    display: "flex"
  },
  welcomeText: {
    color: "#a5b4fc",
    fontSize: 8.5,
    fontWeight: "600"
  },
  userNameText: {
    color: "#ffffff",
    fontSize: 11,
    fontWeight: "800",
    maxWidth: 80
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: "rgba(0, 0, 0, 0.55)",
    justifyContent: "center",
    alignItems: "center",
    padding: 20
  },
  modalCard: {
    width: "100%",
    maxWidth: 360,
    backgroundColor: "#ffffff",
    borderRadius: 16,
    padding: 18,
    shadowColor: "#000",
    shadowOpacity: 0.2,
    shadowRadius: 10,
    elevation: 8
  },
  modalHeader: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 6
  },
  modalTitle: {
    fontSize: 16,
    fontWeight: "800",
    color: "#0f172a"
  },
  modalSubtitle: {
    fontSize: 12,
    color: "#64748b",
    marginBottom: 14,
    lineHeight: 16
  },
  zoneOption: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    padding: 12,
    borderRadius: 10,
    borderWidth: 1,
    borderColor: "#e2e8f0",
    marginBottom: 8,
    backgroundColor: "#f8fafc"
  },
  zoneOptionActive: {
    borderColor: "#86efac",
    backgroundColor: "#f0fdf4"
  },
  zoneRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 10
  },
  zoneName: {
    fontSize: 14,
    fontWeight: "700",
    color: "#334155"
  },
  zoneNameActive: {
    color: "#166534",
    fontWeight: "800"
  }
});
