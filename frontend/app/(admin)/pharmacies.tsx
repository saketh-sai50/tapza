import React, { useState, useEffect } from "react";
import {
  View,
  Text,
  FlatList,
  TouchableOpacity,
  StyleSheet,
  ActivityIndicator,
  RefreshControl,
  Alert
} from "react-native";
import { api } from "../../services/api";
import { Colors, Config } from "../../constants/Config";

export default function AdminPharmaciesScreen() {
  const [pharmacies, setPharmacies] = useState<any[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [refreshing, setRefreshing] = useState<boolean>(false);

  const fetchPharmacies = async () => {
    try {
      const res = await api.get<{ pharmacies: any[] }>("/admin/pharmacies");
      setPharmacies(res.pharmacies);
    } catch (err) {
      console.error("Failed to load pharmacies:", err);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchPharmacies();
  }, []);

  const handleToggleStatus = async (pharmacyId: number, currentActive: boolean) => {
    try {
      await api.post(`/admin/pharmacies/${pharmacyId}/toggle`, {});
      fetchPharmacies();
    } catch (err: any) {
      Alert.alert("Status Update Failed", err.message || "Failed to update pharmacy");
    }
  };

  const handleUpdateZone = (pharmacyId: number, currentZone: string) => {
    Alert.alert(
      "Reassign Pharmacy Zone",
      `Select operating zone for this pharmacy (Current: ${currentZone}):`,
      Config.AVAILABLE_ZONES.map((z) => ({
        text: z,
        onPress: async () => {
          try {
            await api.put(`/admin/pharmacies/${pharmacyId}/zone`, { zone: z });
            fetchPharmacies();
          } catch (err: any) {
            Alert.alert("Zone Update Failed", err.message || "Could not reassign zone");
          }
        }
      })).concat([{ text: "Cancel", style: "cancel" }])
    );
  };

  return (
    <View style={styles.container}>
      {loading ? (
        <View style={styles.center}>
          <ActivityIndicator size="large" color={Colors.primary} />
        </View>
      ) : (
        <FlatList
          data={pharmacies}
          keyExtractor={(item) => String(item.user_id)}
          refreshControl={
            <RefreshControl refreshing={refreshing} onRefresh={() => { setRefreshing(true); fetchPharmacies(); }} />
          }
          contentContainerStyle={{ padding: 14 }}
          renderItem={({ item }) => (
            <View style={styles.pharmacyCard}>
              <View style={styles.cardHeader}>
                <View style={{ flex: 1 }}>
                  <Text style={styles.pharmacyName}>{item.pharmacy_name}</Text>
                  <Text style={styles.licenseText}>License: {item.license_number}</Text>
                  <Text style={styles.addressText}>{item.address}</Text>
                </View>

                <View style={[styles.statusBadge, item.is_active ? styles.activeBadge : styles.inactiveBadge]}>
                  <Text style={[styles.statusBadgeText, item.is_active ? styles.activeBadgeText : styles.inactiveBadgeText]}>
                    {item.is_active ? "VERIFIED ACTIVE" : "SUSPENDED"}
                  </Text>
                </View>
              </View>

              <View style={styles.statsRow}>
                <View style={styles.statItem}>
                  <Text style={styles.statLabel}>Current Zone</Text>
                  <TouchableOpacity onPress={() => handleUpdateZone(item.user_id, item.zone)}>
                    <Text style={styles.zoneLink}>{item.zone} (Change)</Text>
                  </TouchableOpacity>
                </View>
                <View style={styles.statItem}>
                  <Text style={styles.statLabel}>Quotes Submitted</Text>
                  <Text style={styles.statVal}>{item.quotes_submitted_count}</Text>
                </View>
                <View style={styles.statItem}>
                  <Text style={styles.statLabel}>Orders Won</Text>
                  <Text style={styles.statVal}>{item.orders_won_count}</Text>
                </View>
              </View>

              <View style={styles.footerRow}>
                <Text style={styles.contactText}>
                  Pharmacist: {item.full_name} • {item.email}
                </Text>

                <TouchableOpacity
                  style={[styles.toggleBtn, item.is_active ? styles.suspendBtn : styles.activateBtn]}
                  onPress={() => handleToggleStatus(item.user_id, item.is_active)}
                >
                  <Text style={[styles.toggleBtnText, item.is_active ? styles.suspendBtnText : styles.activateBtnText]}>
                    {item.is_active ? "Suspend Access" : "Re-activate"}
                  </Text>
                </TouchableOpacity>
              </View>
            </View>
          )}
        />
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.background
  },
  center: {
    flex: 1,
    justifyContent: "center",
    alignItems: "center"
  },
  pharmacyCard: {
    backgroundColor: "#ffffff",
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: Colors.border,
    shadowColor: "#000",
    shadowOpacity: 0.04,
    shadowOffset: { width: 0, height: 2 },
    shadowRadius: 4,
    elevation: 2
  },
  cardHeader: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "flex-start"
  },
  pharmacyName: {
    fontSize: 16,
    fontWeight: "800",
    color: Colors.text
  },
  licenseText: {
    fontSize: 12,
    fontWeight: "600",
    color: Colors.primaryDark,
    marginTop: 2
  },
  addressText: {
    fontSize: 12,
    color: Colors.textSecondary,
    marginTop: 2
  },
  statusBadge: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 6
  },
  activeBadge: {
    backgroundColor: "#dcfce7"
  },
  inactiveBadge: {
    backgroundColor: "#fee2e2"
  },
  statusBadgeText: {
    fontSize: 10,
    fontWeight: "800",
    letterSpacing: 0.5
  },
  activeBadgeText: {
    color: "#166534"
  },
  inactiveBadgeText: {
    color: Colors.danger
  },
  statsRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    backgroundColor: "#f8fafc",
    padding: 10,
    borderRadius: 8,
    marginVertical: 12
  },
  statItem: {
    alignItems: "center"
  },
  statLabel: {
    fontSize: 10,
    fontWeight: "700",
    color: Colors.textSecondary
  },
  statVal: {
    fontSize: 15,
    fontWeight: "800",
    color: Colors.text,
    marginTop: 2
  },
  zoneLink: {
    fontSize: 13,
    fontWeight: "800",
    color: Colors.primary,
    marginTop: 2
  },
  footerRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    paddingTop: 8,
    borderTopWidth: 1,
    borderTopColor: "#f1f5f9"
  },
  contactText: {
    fontSize: 11,
    color: Colors.textSecondary,
    flex: 1,
    marginRight: 8
  },
  toggleBtn: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 6
  },
  suspendBtn: {
    backgroundColor: "#fee2e2"
  },
  activateBtn: {
    backgroundColor: "#dcfce7"
  },
  toggleBtnText: {
    fontSize: 12,
    fontWeight: "700"
  },
  suspendBtnText: {
    color: Colors.danger
  },
  activateBtnText: {
    color: "#166534"
  }
});
