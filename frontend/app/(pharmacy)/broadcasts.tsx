import React, { useState, useEffect } from "react";
import {
  View,
  Text,
  FlatList,
  TouchableOpacity,
  StyleSheet,
  ActivityIndicator,
  RefreshControl
} from "react-native";
import { api } from "../../services/api";
import { useAuth } from "../../context/AuthContext";
import { Colors } from "../../constants/Config";

export default function PharmacyBroadcastsScreen({ navigation }: any) {
  const { user } = useAuth();
  const [broadcasts, setBroadcasts] = useState<any[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [refreshing, setRefreshing] = useState<boolean>(false);

  const fetchBroadcasts = async () => {
    try {
      const res = await api.get<{ broadcasts: any[] }>("/pharmacy/broadcasts");
      setBroadcasts(res.broadcasts);
    } catch (err) {
      console.error("Failed to fetch broadcasts:", err);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchBroadcasts();
    const interval = setInterval(fetchBroadcasts, 3000);
    return () => clearInterval(interval);
  }, []);

  return (
    <View style={styles.container}>
      {/* Zone Header */}
      <View style={styles.zoneHeader}>
        <View>
          <Text style={styles.zoneTitle}>Active Zone Broadcasts</Text>
          <Text style={styles.zoneSubtitle}>
            Pharmacy: {user?.pharmacy?.pharmacy_name || user?.full_name} • Zone: {user?.zone}
          </Text>
        </View>
        <View style={styles.activePill}>
          <Text style={styles.activePillText}>{broadcasts.length} Active</Text>
        </View>
      </View>

      {loading ? (
        <View style={styles.center}>
          <ActivityIndicator size="large" color={Colors.primary} />
        </View>
      ) : broadcasts.length === 0 ? (
        <View style={styles.emptyContainer}>
          <Text style={styles.emptyTitle}>No active broadcasts right now</Text>
          <Text style={styles.emptySubtitle}>
            When customers in {user?.zone} place orders, they will appear here with an exact 4-minute countdown.
          </Text>
        </View>
      ) : (
        <FlatList
          data={broadcasts}
          keyExtractor={(item) => String(item.order_id)}
          refreshControl={
            <RefreshControl
              refreshing={refreshing}
              onRefresh={() => { setRefreshing(true); fetchBroadcasts(); }}
            />
          }
          contentContainerStyle={{ padding: 14 }}
          renderItem={({ item }) => {
            const mins = Math.floor(item.remaining_broadcast_seconds / 60);
            const secs = item.remaining_broadcast_seconds % 60;
            const timerStr = `${String(mins).padStart(2, "0")}:${String(secs).padStart(2, "0")}`;

            return (
              <View style={styles.orderCard}>
                <View style={styles.cardTop}>
                  <View>
                    <Text style={styles.orderNumber}>Order #{item.order_id}</Text>
                    <Text style={styles.addressText}>{item.delivery_address}</Text>
                  </View>
                  <View style={styles.timerContainer}>
                    <Text style={styles.timerLabel}>WINDOW REMAINING</Text>
                    <Text style={styles.timerValue}>{timerStr}</Text>
                  </View>
                </View>

                {/* Medicine Items List */}
                <View style={styles.itemsSummary}>
                  <Text style={styles.itemsHeading}>
                    Requested Items ({item.items.length}):
                  </Text>
                  {item.items.map((i: any) => (
                    <Text key={i.id} style={styles.itemLine}>
                      • {i.medicine_name} × {i.quantity} (MRP ${i.unit_mrp.toFixed(2)})
                    </Text>
                  ))}
                </View>

                <View style={styles.cardBottom}>
                  <View>
                    <Text style={styles.mrpLabel}>Catalogue Total MRP</Text>
                    <Text style={styles.mrpValue}>${item.total_mrp.toFixed(2)}</Text>
                  </View>

                  {item.already_quoted ? (
                    <View style={styles.quotedBadge}>
                      <Text style={styles.quotedBadgeText}>Quote Submitted</Text>
                    </View>
                  ) : (
                    <TouchableOpacity
                      style={styles.quoteBtn}
                      onPress={() => navigation?.navigate?.("quote/[id]", { id: item.order_id })}
                    >
                      <Text style={styles.quoteBtnText}>Submit Quote &rarr;</Text>
                    </TouchableOpacity>
                  )}
                </View>
              </View>
            );
          }}
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
  zoneHeader: {
    padding: 16,
    backgroundColor: "#ffffff",
    borderBottomWidth: 1,
    borderBottomColor: Colors.border,
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center"
  },
  zoneTitle: {
    fontSize: 16,
    fontWeight: "800",
    color: Colors.text
  },
  zoneSubtitle: {
    fontSize: 12,
    color: Colors.textSecondary,
    marginTop: 2
  },
  activePill: {
    backgroundColor: "#e0f2fe",
    paddingHorizontal: 10,
    paddingVertical: 5,
    borderRadius: 8
  },
  activePillText: {
    color: Colors.primaryDark,
    fontSize: 12,
    fontWeight: "700"
  },
  center: {
    flex: 1,
    justifyContent: "center",
    alignItems: "center"
  },
  emptyContainer: {
    flex: 1,
    justifyContent: "center",
    alignItems: "center",
    padding: 30
  },
  emptyTitle: {
    fontSize: 18,
    fontWeight: "700",
    color: Colors.text
  },
  emptySubtitle: {
    fontSize: 13,
    color: Colors.textSecondary,
    marginTop: 6,
    textAlign: "center",
    lineHeight: 18
  },
  orderCard: {
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
  cardTop: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "flex-start"
  },
  orderNumber: {
    fontSize: 16,
    fontWeight: "800",
    color: Colors.text
  },
  addressText: {
    fontSize: 12,
    color: Colors.textSecondary,
    marginTop: 2
  },
  timerContainer: {
    backgroundColor: "#eff6ff",
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: 8,
    alignItems: "flex-end",
    borderWidth: 1,
    borderColor: "#bfdbfe"
  },
  timerLabel: {
    fontSize: 9,
    fontWeight: "800",
    color: Colors.primaryDark
  },
  timerValue: {
    fontSize: 16,
    fontWeight: "800",
    color: Colors.primaryDark,
    fontVariant: ["tabular-nums"]
  },
  itemsSummary: {
    backgroundColor: "#f8fafc",
    padding: 10,
    borderRadius: 8,
    marginVertical: 12
  },
  itemsHeading: {
    fontSize: 12,
    fontWeight: "700",
    color: Colors.textSecondary,
    marginBottom: 4
  },
  itemLine: {
    fontSize: 13,
    color: Colors.text,
    marginVertical: 1
  },
  cardBottom: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    paddingTop: 8,
    borderTopWidth: 1,
    borderTopColor: "#f1f5f9"
  },
  mrpLabel: {
    fontSize: 11,
    color: Colors.textSecondary
  },
  mrpValue: {
    fontSize: 16,
    fontWeight: "800",
    color: Colors.text
  },
  quotedBadge: {
    backgroundColor: "#dcfce7",
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 8
  },
  quotedBadgeText: {
    color: "#166534",
    fontWeight: "700",
    fontSize: 13
  },
  quoteBtn: {
    backgroundColor: Colors.primary,
    paddingHorizontal: 16,
    paddingVertical: 10,
    borderRadius: 8
  },
  quoteBtnText: {
    color: "#ffffff",
    fontWeight: "700",
    fontSize: 13
  }
});
