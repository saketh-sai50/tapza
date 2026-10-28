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
import { Colors } from "../../constants/Config";

export default function AdminOrdersAuditScreen() {
  const [orders, setOrders] = useState<any[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [refreshing, setRefreshing] = useState<boolean>(false);
  const [selectedStatus, setSelectedStatus] = useState<string>("");

  const fetchOrders = async () => {
    try {
      let query = "/admin/orders?";
      if (selectedStatus) query += `status=${encodeURIComponent(selectedStatus)}`;
      const res = await api.get<{ orders: any[] }>(query);
      setOrders(res.orders);
    } catch (err) {
      console.error("Failed to load audit orders:", err);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchOrders();
  }, [selectedStatus]);

  const statusList = [
    "",
    "BROADCASTING",
    "PENDING_SELECTION",
    "CONFIRMED_PENDING_PHARMACY",
    "CONFIRMED",
    "DELIVERED",
    "CANCELLED",
    "REJECTED"
  ];

  return (
    <View style={styles.container}>
      {/* Filter Chips */}
      <View style={styles.filterBar}>
        {statusList.map((stg) => (
          <TouchableOpacity
            key={stg}
            style={[styles.filterChip, selectedStatus === stg && styles.filterChipActive]}
            onPress={() => setSelectedStatus(stg)}
          >
            <Text style={[styles.filterChipText, selectedStatus === stg && styles.filterChipTextActive]}>
              {stg ? stg.replace(/_/g, " ") : "All Statuses"}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      {loading ? (
        <View style={styles.center}>
          <ActivityIndicator size="large" color={Colors.primary} />
        </View>
      ) : orders.length === 0 ? (
        <View style={styles.emptyContainer}>
          <Text style={styles.emptyTitle}>No orders match filter</Text>
        </View>
      ) : (
        <FlatList
          data={orders}
          keyExtractor={(item) => String(item.id)}
          refreshControl={
            <RefreshControl refreshing={refreshing} onRefresh={() => { setRefreshing(true); fetchOrders(); }} />
          }
          contentContainerStyle={{ padding: 14 }}
          renderItem={({ item }) => (
            <View style={styles.orderCard}>
              <View style={styles.cardHeader}>
                <View>
                  <Text style={styles.orderId}>Order #{item.id}</Text>
                  <Text style={styles.customerName}>
                    Customer: {item.customer.name} ({item.customer.email})
                  </Text>
                </View>
                <View style={styles.statusPill}>
                  <Text style={styles.statusPillText}>{item.status.replace(/_/g, " ")}</Text>
                </View>
              </View>

              <View style={styles.detailsGrid}>
                <Text style={styles.metaItem}>Zone: {item.zone}</Text>
                <Text style={styles.metaItem}>Quotes: {item.quote_count}</Text>
                <Text style={styles.metaItem}>Items: {item.item_count}</Text>
                <Text style={styles.metaItem}>Mock Payment: {item.mock_payment_status}</Text>
              </View>

              {item.assigned_pharmacy ? (
                <View style={styles.assignedBox}>
                  <Text style={styles.assignedText}>
                    Assigned: {item.assigned_pharmacy.name} ({item.assigned_pharmacy.confirmation_status})
                  </Text>
                </View>
              ) : null}

              <View style={styles.cardFooter}>
                <Text style={styles.dateText}>{item.created_at}</Text>
                <Text style={styles.amountText}>Final: ${item.final_amount.toFixed(2)}</Text>
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
  filterBar: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 6,
    padding: 12,
    backgroundColor: "#ffffff",
    borderBottomWidth: 1,
    borderBottomColor: Colors.border
  },
  filterChip: {
    paddingHorizontal: 10,
    paddingVertical: 5,
    borderRadius: 6,
    backgroundColor: "#f1f5f9"
  },
  filterChipActive: {
    backgroundColor: Colors.primary
  },
  filterChipText: {
    fontSize: 11,
    fontWeight: "700",
    color: Colors.textSecondary
  },
  filterChipTextActive: {
    color: "#ffffff"
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
    padding: 24
  },
  emptyTitle: {
    fontSize: 16,
    fontWeight: "700",
    color: Colors.textSecondary
  },
  orderCard: {
    backgroundColor: "#ffffff",
    borderRadius: 10,
    padding: 14,
    marginBottom: 10,
    borderWidth: 1,
    borderColor: Colors.border
  },
  cardHeader: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "flex-start"
  },
  orderId: {
    fontSize: 15,
    fontWeight: "800",
    color: Colors.text
  },
  customerName: {
    fontSize: 12,
    color: Colors.textSecondary,
    marginTop: 2
  },
  statusPill: {
    backgroundColor: "#e0f2fe",
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 4
  },
  statusPillText: {
    fontSize: 10,
    fontWeight: "800",
    color: Colors.primaryDark
  },
  detailsGrid: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 12,
    marginVertical: 8
  },
  metaItem: {
    fontSize: 12,
    color: Colors.textSecondary
  },
  assignedBox: {
    backgroundColor: "#f0fdf4",
    padding: 6,
    borderRadius: 4,
    marginBottom: 6
  },
  assignedText: {
    fontSize: 12,
    color: "#166534",
    fontWeight: "600"
  },
  cardFooter: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    borderTopWidth: 1,
    borderTopColor: "#f1f5f9",
    paddingTop: 6
  },
  dateText: {
    fontSize: 11,
    color: Colors.textSecondary
  },
  amountText: {
    fontSize: 15,
    fontWeight: "800",
    color: Colors.text
  }
});
