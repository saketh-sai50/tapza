import React, { useState, useEffect } from "react";
import {
  View,
  Text,
  ScrollView,
  StyleSheet,
  ActivityIndicator,
  RefreshControl,
  TouchableOpacity
} from "react-native";
import { api } from "../../services/api";
import { Colors } from "../../constants/Config";

export default function AdminDashboardScreen({ navigation }: any) {
  const [metrics, setMetrics] = useState<any>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [refreshing, setRefreshing] = useState<boolean>(false);

  const fetchMetrics = async () => {
    try {
      const res = await api.get<{ metrics: any }>("/admin/metrics");
      setMetrics(res.metrics);
    } catch (err) {
      console.error("Failed to load admin metrics:", err);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchMetrics();
  }, []);

  if (loading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator size="large" color={Colors.primary} />
      </View>
    );
  }

  return (
    <ScrollView
      style={styles.container}
      contentContainerStyle={{ padding: 16, paddingBottom: 60 }}
      refreshControl={
        <RefreshControl refreshing={refreshing} onRefresh={() => { setRefreshing(true); fetchMetrics(); }} />
      }
    >
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Tapza Admin Console</Text>
        <Text style={styles.headerSubtitle}>Real-time platform operations & analytics</Text>
      </View>

      {/* Primary KPI Grid */}
      <View style={styles.kpiGrid}>
        <View style={styles.kpiCard}>
          <Text style={styles.kpiLabel}>TOTAL PLATFORM GMV</Text>
          <Text style={styles.kpiValue}>${metrics?.platform_gmv?.toFixed(2) || "0.00"}</Text>
          <Text style={styles.kpiSub}>Fulfilled order volume</Text>
        </View>

        <View style={styles.kpiCard}>
          <Text style={styles.kpiLabel}>ACTIVE BROADCASTS</Text>
          <Text style={[styles.kpiValue, { color: Colors.primaryDark }]}>
            {metrics?.orders?.active_broadcasts || 0}
          </Text>
          <Text style={styles.kpiSub}>4-min quoting in progress</Text>
        </View>

        <View style={styles.kpiCard}>
          <Text style={styles.kpiLabel}>ORDERS FULFILLED</Text>
          <Text style={[styles.kpiValue, { color: Colors.secondary }]}>
            {metrics?.orders?.delivered || 0}
          </Text>
          <Text style={styles.kpiSub}>Completed deliveries</Text>
        </View>

        <View style={styles.kpiCard}>
          <Text style={styles.kpiLabel}>ACTIVE PHARMACIES</Text>
          <Text style={styles.kpiValue}>
            {metrics?.users?.active_pharmacies || 0} / {metrics?.users?.pharmacies || 0}
          </Text>
          <Text style={styles.kpiSub}>Verified dispensaries</Text>
        </View>
      </View>

      {/* Zone Distribution */}
      <View style={styles.sectionCard}>
        <Text style={styles.sectionTitle}>Zone Activity Distribution</Text>
        {metrics?.zones?.map((z: any) => (
          <View key={z.zone} style={styles.zoneRow}>
            <View>
              <Text style={styles.zoneName}>{z.zone}</Text>
              <Text style={styles.zoneMeta}>{z.order_count} orders processed</Text>
            </View>
            <Text style={styles.zoneVol}>${z.zone_volume.toFixed(2)}</Text>
          </View>
        ))}
      </View>

      {/* Quick Navigation Cards */}
      <View style={styles.sectionCard}>
        <Text style={styles.sectionTitle}>Management Modules</Text>

        <TouchableOpacity
          style={styles.navItem}
          onPress={() => navigation?.navigate?.("pharmacies")}
        >
          <View>
            <Text style={styles.navTitle}>Pharmacy Verification & Zones</Text>
            <Text style={styles.navSub}>Activate licenses, manage service areas</Text>
          </View>
          <Text style={styles.navArrow}>&rarr;</Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={styles.navItem}
          onPress={() => navigation?.navigate?.("orders")}
        >
          <View>
            <Text style={styles.navTitle}>Global Order Audit Trail</Text>
            <Text style={styles.navSub}>View customer orders, quotes, and fulfillment status</Text>
          </View>
          <Text style={styles.navArrow}>&rarr;</Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={styles.navItem}
          onPress={() => navigation?.navigate?.("medicines")}
        >
          <View>
            <Text style={styles.navTitle}>Medicine Catalogue & Excel Import</Text>
            <Text style={styles.navSub}>Manage authorized medicines, upload .xlsx batches</Text>
          </View>
          <Text style={styles.navArrow}>&rarr;</Text>
        </TouchableOpacity>
      </View>
    </ScrollView>
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
  header: {
    marginBottom: 16
  },
  headerTitle: {
    fontSize: 22,
    fontWeight: "900",
    color: Colors.text
  },
  headerSubtitle: {
    fontSize: 13,
    color: Colors.textSecondary,
    marginTop: 2
  },
  kpiGrid: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 12,
    marginBottom: 16
  },
  kpiCard: {
    flex: 1,
    minWidth: 150,
    backgroundColor: "#ffffff",
    borderRadius: 12,
    padding: 16,
    borderWidth: 1,
    borderColor: Colors.border,
    shadowColor: "#000",
    shadowOpacity: 0.04,
    shadowOffset: { width: 0, height: 2 },
    shadowRadius: 4,
    elevation: 2
  },
  kpiLabel: {
    fontSize: 10,
    fontWeight: "800",
    color: Colors.textSecondary,
    letterSpacing: 0.5
  },
  kpiValue: {
    fontSize: 22,
    fontWeight: "900",
    color: Colors.text,
    marginVertical: 4
  },
  kpiSub: {
    fontSize: 11,
    color: Colors.textSecondary
  },
  sectionCard: {
    backgroundColor: "#ffffff",
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: Colors.border
  },
  sectionTitle: {
    fontSize: 15,
    fontWeight: "800",
    color: Colors.text,
    marginBottom: 12
  },
  zoneRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    paddingVertical: 8,
    borderBottomWidth: 1,
    borderBottomColor: "#f1f5f9"
  },
  zoneName: {
    fontSize: 14,
    fontWeight: "700",
    color: Colors.text
  },
  zoneMeta: {
    fontSize: 12,
    color: Colors.textSecondary,
    marginTop: 1
  },
  zoneVol: {
    fontSize: 15,
    fontWeight: "800",
    color: Colors.primaryDark
  },
  navItem: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: "#f1f5f9"
  },
  navTitle: {
    fontSize: 14,
    fontWeight: "700",
    color: Colors.text
  },
  navSub: {
    fontSize: 12,
    color: Colors.textSecondary,
    marginTop: 2
  },
  navArrow: {
    fontSize: 18,
    fontWeight: "700",
    color: Colors.primaryDark
  }
});
