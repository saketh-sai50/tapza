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
import { Order } from "../../../types";
import { api } from "../../../services/api";
import { Colors } from "../../../constants/Config";

export default function CustomerOrdersListScreen({ navigation }: any) {
  const [orders, setOrders] = useState<Order[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [refreshing, setRefreshing] = useState<boolean>(false);

  const fetchOrders = async () => {
    try {
      const res = await api.get<{ orders: Order[] }>("/orders/my-orders");
      setOrders(res.orders);
    } catch (err) {
      console.error("Failed to load orders:", err);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchOrders();
    const interval = setInterval(fetchOrders, 5000); // Poll status updates
    return () => clearInterval(interval);
  }, []);

  const getStatusColor = (status: string) => {
    switch (status) {
      case "BROADCASTING":
        return Colors.primary;
      case "PENDING_SELECTION":
        return Colors.warning;
      case "CONFIRMED":
      case "CONFIRMED_PENDING_PHARMACY":
        return Colors.success;
      case "DISPATCHED":
      case "DELIVERED":
        return Colors.secondary;
      case "CANCELLED":
      case "EXPIRED":
      case "REJECTED":
        return Colors.danger;
      default:
        return Colors.textSecondary;
    }
  };

  return (
    <View style={styles.container}>
      {loading ? (
        <View style={styles.center}>
          <ActivityIndicator size="large" color={Colors.primary} />
        </View>
      ) : orders.length === 0 ? (
        <View style={styles.emptyContainer}>
          <Text style={styles.emptyTitle}>No orders yet</Text>
          <Text style={styles.emptySub}>Place an order to start receiving competitive pharmacy quotes.</Text>
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
            <TouchableOpacity
              style={styles.orderCard}
              onPress={() => navigation?.navigate?.("orders/[id]", { id: item.id })}
            >
              <View style={styles.cardTop}>
                <View>
                  <Text style={styles.orderNumber}>Order #{item.id}</Text>
                  <Text style={styles.orderDate}>{item.created_at}</Text>
                </View>
                <View style={[styles.statusBadge, { backgroundColor: `${getStatusColor(item.status)}20` }]}>
                  <Text style={[styles.statusText, { color: getStatusColor(item.status) }]}>
                    {item.status.replace(/_/g, " ")}
                  </Text>
                </View>
              </View>

              <View style={styles.cardMid}>
                <Text style={styles.detailText}>
                  Zone: {item.zone} • {item.item_count || 1} item(s)
                </Text>
                {item.status === "BROADCASTING" && item.remaining_broadcast_seconds > 0 && (
                  <Text style={styles.liveTimerText}>
                    ⏱ Broadcast ends in {Math.floor(item.remaining_broadcast_seconds / 60)}m {item.remaining_broadcast_seconds % 60}s
                  </Text>
                )}
                {item.assigned_pharmacy && (
                  <Text style={styles.pharmacyWonText}>
                    Fulfilled by: {item.assigned_pharmacy.name}
                  </Text>
                )}
              </View>

              <View style={styles.cardBottom}>
                <Text style={styles.quoteCount}>
                  {item.quote_count || 0} quote(s) received
                </Text>
                <Text style={styles.amountText}>
                  ${item.final_amount ? item.final_amount.toFixed(2) : item.total_mrp.toFixed(2)}
                </Text>
              </View>
            </TouchableOpacity>
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
  emptyContainer: {
    flex: 1,
    justifyContent: "center",
    alignItems: "center",
    padding: 24
  },
  emptyTitle: {
    fontSize: 18,
    fontWeight: "700",
    color: Colors.text
  },
  emptySub: {
    fontSize: 13,
    color: Colors.textSecondary,
    marginTop: 4,
    textAlign: "center"
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
    fontWeight: "700",
    color: Colors.text
  },
  orderDate: {
    fontSize: 12,
    color: Colors.textSecondary,
    marginTop: 2
  },
  statusBadge: {
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 6
  },
  statusText: {
    fontSize: 11,
    fontWeight: "800",
    letterSpacing: 0.5
  },
  cardMid: {
    marginVertical: 10
  },
  detailText: {
    fontSize: 13,
    color: Colors.textSecondary
  },
  liveTimerText: {
    fontSize: 13,
    color: Colors.primaryDark,
    fontWeight: "700",
    marginTop: 4
  },
  pharmacyWonText: {
    fontSize: 13,
    color: Colors.secondary,
    fontWeight: "700",
    marginTop: 4
  },
  cardBottom: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    paddingTop: 10,
    borderTopWidth: 1,
    borderTopColor: "#f1f5f9"
  },
  quoteCount: {
    fontSize: 13,
    color: Colors.textSecondary,
    fontWeight: "600"
  },
  amountText: {
    fontSize: 16,
    fontWeight: "800",
    color: Colors.text
  }
});
