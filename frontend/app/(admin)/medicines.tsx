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
import { Medicine } from "../../types";
import { api } from "../../services/api";
import { Colors } from "../../constants/Config";

export default function AdminMedicinesScreen() {
  const [medicines, setMedicines] = useState<Medicine[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [refreshing, setRefreshing] = useState<boolean>(false);

  const fetchMedicines = async () => {
    try {
      const res = await api.get<{ medicines: Medicine[] }>("/medicines?limit=100");
      setMedicines(res.medicines);
    } catch (err) {
      console.error("Failed to load medicines:", err);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchMedicines();
  }, []);

  const handleDeactivate = (medId: number, name: string) => {
    Alert.alert(
      "Deactivate Medicine",
      `Are you sure you want to soft-delete '${name}'? Existing past orders will remain intact.`,
      [
        { text: "Cancel", style: "cancel" },
        {
          text: "Deactivate",
          style: "destructive",
          onPress: async () => {
            try {
              await api.delete(`/medicines/${medId}`);
              fetchMedicines();
            } catch (err: any) {
              Alert.alert("Deactivation Failed", err.message || "Could not delete");
            }
          }
        }
      ]
    );
  };

  return (
    <View style={styles.container}>
      {/* Excel Import & Template Header Card */}
      <View style={styles.importBanner}>
        <View style={{ flex: 1, paddingRight: 8 }}>
          <Text style={styles.bannerTitle}>Bulk Medicine Catalogue Sync</Text>
          <Text style={styles.bannerSub}>
            Import medicines in bulk via validated Excel (.xlsx) spreadsheets with positive MRP checks.
          </Text>
        </View>

        <View style={styles.bannerActions}>
          <TouchableOpacity
            style={styles.templateBtn}
            onPress={() => {
              Alert.alert(
                "Starter Template",
                "Template endpoint: /api/medicines/template\n\nColumns: Name, Generic Name, Manufacturer, Category, Dosage Form, Pack Size, MRP, Requires Prescription."
              );
            }}
          >
            <Text style={styles.templateBtnText}>Excel Template</Text>
          </TouchableOpacity>
        </View>
      </View>

      {loading ? (
        <View style={styles.center}>
          <ActivityIndicator size="large" color={Colors.primary} />
        </View>
      ) : (
        <FlatList
          data={medicines}
          keyExtractor={(item) => String(item.id)}
          refreshControl={
            <RefreshControl refreshing={refreshing} onRefresh={() => { setRefreshing(true); fetchMedicines(); }} />
          }
          contentContainerStyle={{ padding: 14 }}
          renderItem={({ item }) => (
            <View style={styles.medCard}>
              <View style={styles.medTop}>
                <View style={{ flex: 1 }}>
                  <Text style={styles.medName}>{item.name}</Text>
                  <Text style={styles.medMeta}>
                    {item.category} • {item.dosage_form || "Form"} • {item.pack_size || "Unit"}
                  </Text>
                  {item.requires_prescription && (
                    <Text style={styles.rxFlag}>Rx Required</Text>
                  )}
                </View>

                <View style={{ alignItems: "flex-end" }}>
                  <Text style={styles.mrpLabel}>Standard MRP</Text>
                  <Text style={styles.mrpVal}>${item.mrp.toFixed(2)}</Text>
                </View>
              </View>

              <View style={styles.medBottom}>
                <Text style={styles.manufacturerText}>
                  Manufacturer: {item.manufacturer || "N/A"}
                </Text>

                <TouchableOpacity
                  style={styles.deactivateBtn}
                  onPress={() => handleDeactivate(item.id, item.name)}
                >
                  <Text style={styles.deactivateBtnText}>Deactivate</Text>
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
  importBanner: {
    backgroundColor: "#eff6ff",
    borderRadius: 12,
    padding: 16,
    margin: 14,
    borderWidth: 1,
    borderColor: "#bfdbfe",
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center"
  },
  bannerTitle: {
    fontSize: 15,
    fontWeight: "800",
    color: "#1e3a8a"
  },
  bannerSub: {
    fontSize: 12,
    color: "#1e40af",
    marginTop: 2
  },
  bannerActions: {
    alignItems: "flex-end"
  },
  templateBtn: {
    backgroundColor: Colors.primary,
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 6
  },
  templateBtnText: {
    color: "#ffffff",
    fontWeight: "700",
    fontSize: 12
  },
  center: {
    flex: 1,
    justifyContent: "center",
    alignItems: "center"
  },
  medCard: {
    backgroundColor: "#ffffff",
    borderRadius: 10,
    padding: 14,
    marginBottom: 10,
    borderWidth: 1,
    borderColor: Colors.border
  },
  medTop: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "flex-start"
  },
  medName: {
    fontSize: 15,
    fontWeight: "700",
    color: Colors.text
  },
  medMeta: {
    fontSize: 12,
    color: Colors.textSecondary,
    marginTop: 2
  },
  rxFlag: {
    fontSize: 10,
    fontWeight: "800",
    color: Colors.danger,
    marginTop: 2
  },
  mrpLabel: {
    fontSize: 10,
    color: Colors.textSecondary
  },
  mrpVal: {
    fontSize: 16,
    fontWeight: "800",
    color: Colors.primaryDark
  },
  medBottom: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginTop: 8,
    paddingTop: 8,
    borderTopWidth: 1,
    borderTopColor: "#f1f5f9"
  },
  manufacturerText: {
    fontSize: 12,
    color: Colors.textSecondary
  },
  deactivateBtn: {
    paddingHorizontal: 8,
    paddingVertical: 4
  },
  deactivateBtnText: {
    color: Colors.danger,
    fontSize: 12,
    fontWeight: "600"
  }
});
