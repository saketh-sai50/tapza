import React from "react";
import {
  View,
  Text,
  TouchableOpacity,
  ScrollView,
  StyleSheet,
  Alert
} from "react-native";
import { Ionicons, MaterialCommunityIcons } from "@expo/vector-icons";
import { useApp } from "../context/AppContext";

export const ProfileScreen = ({ onOpenAuth }) => {
  const { user, token, zone, updateZone, logout } = useApp();

  const handleLogoutPress = () => {
    Alert.alert(
      "Confirm Logout",
      "Are you sure you want to log out of your Tapza account?",
      [
        { text: "Cancel", style: "cancel" },
        {
          text: "Yes, Log Out",
          style: "destructive",
          onPress: async () => {
            await logout();
            Alert.alert("Logged Out", "You have been logged out successfully.");
          }
        }
      ]
    );
  };

  return (
    <ScrollView style={styles.container} contentContainerStyle={{ padding: 16 }}>
      {/* Profile Card */}
      <View style={styles.profileCard}>
        <View style={styles.avatarLarge}>
          <Text style={styles.avatarLargeText}>
            {user?.full_name ? user.full_name[0].toUpperCase() : "G"}
          </Text>
        </View>
        <View style={{ flex: 1 }}>
          <Text style={styles.profileName}>
            {user ? user.full_name : "Guest Customer"}
          </Text>
          <Text style={styles.profileEmail}>
            {user ? user.email : "Not logged in"}
          </Text>
          <View style={styles.rolePill}>
            <Text style={styles.rolePillText}>
              {user?.role === "PHARMACY" ? "LICENSED PHARMACY PARTNER" : "VERIFIED CUSTOMER"}
            </Text>
          </View>
        </View>
      </View>

      {/* Auth Action if Guest */}
      {!token && (
        <TouchableOpacity style={styles.loginCard} activeOpacity={0.85} onPress={onOpenAuth}>
          <View style={{ flex: 1 }}>
            <Text style={styles.loginCardTitle}>Log In to Your Account</Text>
            <Text style={styles.loginCardSub}>
              Access orders, live reverse-auction bidding, and faster checkout.
            </Text>
          </View>
          <View style={styles.loginCardBtn}>
            <Text style={styles.loginCardBtnText}>Log In</Text>
          </View>
        </TouchableOpacity>
      )}

      {/* Settings Sections */}
      <View style={styles.sectionCard}>
        <Text style={styles.sectionHeader}>Delivery & Location Preferences</Text>

        <View style={styles.settingRow}>
          <View style={styles.settingIconWrap}>
            <Ionicons name="location-outline" size={18} color="#16a34a" />
          </View>
          <View style={{ flex: 1 }}>
            <Text style={styles.settingTitle}>Current Delivery Zone</Text>
            <Text style={styles.settingSub}>{zone} Fast Delivery Area</Text>
          </View>
          <View style={styles.zoneChips}>
            {["Warangal", "Hanamkonda", "Kazipet"].map((z) => (
              <TouchableOpacity
                key={z}
                style={[styles.zoneChip, zone === z && styles.zoneChipActive]}
                onPress={() => updateZone(z)}
              >
                <Text style={[styles.zoneChipText, zone === z && styles.zoneChipTextActive]}>
                  {z}
                </Text>
              </TouchableOpacity>
            ))}
          </View>
        </View>
      </View>

      <View style={styles.sectionCard}>
        <Text style={styles.sectionHeader}>App & Trust Information</Text>

        <View style={styles.infoRow}>
          <Ionicons name="shield-checkmark-outline" size={18} color="#059669" />
          <View style={{ flex: 1 }}>
            <Text style={styles.infoTitle}>100% Genuine Medicines Guarantee</Text>
            <Text style={styles.infoSub}>
              All bids are sourced exclusively from verified, licensed physical pharmacies in your zone.
            </Text>
          </View>
        </View>

        <View style={styles.infoRow}>
          <MaterialCommunityIcons name="lightning-bolt-outline" size={18} color="#d97706" />
          <View style={{ flex: 1 }}>
            <Text style={styles.infoTitle}>4-Minute Reverse Auction</Text>
            <Text style={styles.infoSub}>
              Local pharmacies compete to offer you competitive discounts below standard MRP.
            </Text>
          </View>
        </View>
      </View>

      {/* Logout Button */}
      {token && (
        <TouchableOpacity style={styles.logoutBtn} activeOpacity={0.8} onPress={handleLogoutPress}>
          <Ionicons name="log-out-outline" size={18} color="#dc2626" />
          <Text style={styles.logoutBtnText}>Log Out</Text>
        </TouchableOpacity>
      )}

      <Text style={styles.versionText}>Tapza Mobile App • React Native v1.0.0</Text>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#f8fafc"
  },
  profileCard: {
    backgroundColor: "#ffffff",
    borderRadius: 14,
    borderWidth: 1,
    borderColor: "#e2e8f0",
    padding: 16,
    flexDirection: "row",
    alignItems: "center",
    gap: 14,
    marginBottom: 14
  },
  avatarLarge: {
    width: 52,
    height: 52,
    borderRadius: 26,
    backgroundColor: "#1e1b4b",
    alignItems: "center",
    justifyContent: "center"
  },
  avatarLargeText: {
    color: "#ffffff",
    fontSize: 22,
    fontWeight: "900"
  },
  profileName: {
    fontSize: 16,
    fontWeight: "900",
    color: "#0f172a"
  },
  profileEmail: {
    fontSize: 12,
    color: "#64748b",
    marginTop: 2
  },
  rolePill: {
    alignSelf: "flex-start",
    backgroundColor: "#ecfdf5",
    borderWidth: 1,
    borderColor: "#a7f3d0",
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 6,
    marginTop: 6
  },
  rolePillText: {
    fontSize: 9.5,
    fontWeight: "800",
    color: "#065f46"
  },
  loginCard: {
    backgroundColor: "#1e1b4b",
    borderRadius: 12,
    padding: 16,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    marginBottom: 14
  },
  loginCardTitle: {
    color: "#ffffff",
    fontSize: 14,
    fontWeight: "800"
  },
  loginCardSub: {
    color: "#a5b4fc",
    fontSize: 11,
    marginTop: 2
  },
  loginCardBtn: {
    backgroundColor: "#10b981",
    paddingVertical: 6,
    paddingHorizontal: 12,
    borderRadius: 8
  },
  loginCardBtnText: {
    color: "#ffffff",
    fontSize: 12,
    fontWeight: "800"
  },
  sectionCard: {
    backgroundColor: "#ffffff",
    borderRadius: 14,
    borderWidth: 1,
    borderColor: "#e2e8f0",
    padding: 16,
    marginBottom: 14
  },
  sectionHeader: {
    fontSize: 13,
    fontWeight: "800",
    color: "#0f172a",
    marginBottom: 12
  },
  settingRow: {
    flexDirection: "column",
    gap: 8
  },
  settingIconWrap: {
    display: "none"
  },
  settingTitle: {
    fontSize: 12,
    fontWeight: "700",
    color: "#334155"
  },
  settingSub: {
    fontSize: 11,
    color: "#64748b",
    marginTop: 1
  },
  zoneChips: {
    flexDirection: "row",
    gap: 8,
    marginTop: 6
  },
  zoneChip: {
    backgroundColor: "#f1f5f9",
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: "#cbd5e1"
  },
  zoneChipActive: {
    backgroundColor: "#ecfdf5",
    borderColor: "#86efac"
  },
  zoneChipText: {
    fontSize: 11.5,
    fontWeight: "700",
    color: "#64748b"
  },
  zoneChipTextActive: {
    color: "#166534",
    fontWeight: "800"
  },
  infoRow: {
    flexDirection: "row",
    alignItems: "flex-start",
    gap: 10,
    marginBottom: 12
  },
  infoTitle: {
    fontSize: 12.5,
    fontWeight: "800",
    color: "#0f172a"
  },
  infoSub: {
    fontSize: 11,
    color: "#64748b",
    marginTop: 2,
    lineHeight: 15
  },
  logoutBtn: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 8,
    backgroundColor: "#fee2e2",
    borderWidth: 1,
    borderColor: "#fca5a5",
    paddingVertical: 12,
    borderRadius: 12,
    marginBottom: 14
  },
  logoutBtnText: {
    color: "#dc2626",
    fontSize: 13.5,
    fontWeight: "800"
  },
  versionText: {
    textAlign: "center",
    fontSize: 11,
    color: "#94a3b8",
    paddingVertical: 10
  }
});
