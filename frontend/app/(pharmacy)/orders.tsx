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
import { Colors } from "../../constants/Config";

export default function PharmacyOrdersScreen() {
  const [orders, setOrders] = useState<any[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [refreshing, setRefreshing] = useState<boolean>(false);
  const [activeTab, setActiveTab] = useState<string>("PENDING");

  const fetchOrders = async () => {
    try {
      const res = await api.get<{ assigned_orders: any[] }>("/pharmacy/orders");
      setOrders(res.assigned_orders);
    } catch (err) {
      console.error("Failed to load pharmacy orders:", err);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchOrders();
    const interval = setInterval(fetchOrders, 4000);
    return () => clearInterval(interval);
  }, []);

  const handleConfirmOrReject = (orderId: number, action: "CONFIRM" | "REJECT") => {
    const isConfirm = action === "CONFIRM";
    Alert.alert(
      isConfirm ? "Confirm Order" : "Reject Order",
      isConfirm
        ? "Do you confirm you have all quoted medicines and will fulfill this order?"
        : "Are you sure you want to reject this order? The customer will be notified.",
      [
        { text: "Cancel", style: "cancel" },
        {
          text: isConfirm ? "Confirm Order" : "Reject Order",
          style: isConfirm ? "default" : "destructive",
          onPress: async () => {
            try {
              await api.post(`/pharmacy/orders/${orderId}/confirm`, { action });
              fetchOrders();
            } catch (err: any) {
              Alert.alert("Action Failed", err.message || "Failed to update order");
            }
          }
        }
      ]
    );
  };

  const handleUpdateStatus = async (orderId: number, nextStatus: string) => {
    try {
      await api.post(`/pharmacy/orders/${orderId}/status`, { status: nextStatus });
      fetchOrders();
    } catch (err: any) {
      Alert.alert("Update Failed", err.message || "Could not update status");
    }
  };

  const filteredOrders = orders.filter((o) => {
    if (activeTab === "PENDING") return o.confirmation_status === "PENDING";
    if (activeTab === "IN_PROGRESS") return ["CONFIRMED", "PREPARING", "DISPATCHED"].includes(o.order_status);
    if (activeTab === "DELIVERED") return o.order_status === "DELIVERED";
    if (activeTab === "REJECTED") return o.order_status === "REJECTED" || o.confirmation_status === "REJECTED";
    return true;
  });

  return (
    <View style={styles.container}>
      {/* Tabs */}
      <View style={styles.tabBar}>
        {["PENDING", "IN_PROGRESS", "DELIVERED", "ALL"].map((tab) => (
          <TouchableOpacity
            key={tab}
            style={[styles.tabItem, activeTab === tab && styles.tabItemActive]}
            onPress={() => setActiveTab(tab)}
          >
            <Text style={[styles.tabText, activeTab === tab && styles.tabTextActive]}>
              {tab.replace("_", " ")}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      {loading ? (
        <View style={styles.center}>
          <ActivityIndicator size="large" color={Colors.primary} />
        </View>
      ) : filteredOrders.length === 0 ? (
        <View style={styles.emptyContainer}>
          <Text style={styles.emptyTitle}>No orders in {activeTab.replace("_", " ")}</Text>
          <Text style={styles.emptySubtitle}>Orders awarded to your pharmacy will appear here.</Text>
        </View>
      ) : (
        <FlatList
          data={filteredOrders}
          keyExtractor={(item) => String(item.order_id)}
          refreshControl={
            <RefreshControl refreshing={refreshing} onRefresh={() => { setRefreshing(true); fetchOrders(); }} />
          }
          contentContainerStyle={{ padding: 14, paddingBottom: 40 }}
          renderItem={({ item }) => {
            const isPending = item.confirmation_status === "PENDING";
            const orderStatus = item.order_status;

            return (
              <View style={styles.orderCard}>
                <View style={styles.cardHeader}>
                  <View>
                    <Text style={styles.orderTitle}>Order #{item.order_id}</Text>
                    <Text style={styles.customerName}>
                      Customer: {item.customer.name} ({item.customer.phone || "No phone"})
                    </Text>
                  </View>
                  <View style={styles.statusBadge}>
                    <Text style={styles.statusBadgeText}>
                      {isPending ? "PENDING CONFIRMATION" : orderStatus}
                    </Text>
                  </View>
                </View>

                <Text style={styles.addressText}>Deliver to: {item.customer.delivery_address}</Text>

                {/* Items Quoted */}
                <View style={styles.itemsBox}>
                  <Text style={styles.itemsTitle}>
                    Quoted Medicines ({item.fulfillment.is_full ? "Full Fulfillment" : `Partial: ${item.fulfillment.available_items_count}/${item.fulfillment.total_items_count}`}):
                  </Text>
                  {item.items.map((i: any, idx: number) => (
                    <View key={idx} style={styles.itemRow}>
                      <Text
                        style={[
                          styles.itemName,
                          !i.is_available && styles.itemUnavailable
                        ]}
                      >
                        • {i.medicine_name} × {i.quantity}
                      </Text>
                      <Text style={styles.itemPrice}>
                        {i.is_available ? `$${i.subtotal_price.toFixed(2)}` : "$0.00 (Out of Stock)"}
                      </Text>
                    </View>
                  ))}
                </View>

                {/* Amount & Actions */}
                <View style={styles.footerRow}>
                  <View>
                    <Text style={styles.amountLabel}>Total Quoted Value</Text>
                    <Text style={styles.amountVal}>${item.final_amount.toFixed(2)}</Text>
                  </View>

                  {/* Pending Confirmation Actions */}
                  {isPending && (
                    <View style={styles.actionBtnRow}>
                      <TouchableOpacity
                        style={styles.rejectBtn}
                        onPress={() => handleConfirmOrReject(item.order_id, "REJECT")}
                      >
                        <Text style={styles.rejectBtnText}>Reject</Text>
                      </TouchableOpacity>
                      <TouchableOpacity
                        style={styles.confirmBtn}
                        onPress={() => handleConfirmOrReject(item.order_id, "CONFIRM")}
                      >
                        <Text style={styles.confirmBtnText}>Confirm Order</Text>
                      </TouchableOpacity>
                    </View>
                  )}

                  {/* Confirmed / Progression Actions */}
                  {!isPending && orderStatus === "CONFIRMED" && (
                    <TouchableOpacity
                      style={styles.progressBtn}
                      onPress={() => handleUpdateStatus(item.order_id, "PREPARING")}
                    >
                      <Text style={styles.progressBtnText}>Start Preparing &rarr;</Text>
                    </TouchableOpacity>
                  )}

                  {!isPending && orderStatus === "PREPARING" && (
                    <TouchableOpacity
                      style={styles.progressBtn}
                      onPress={() => handleUpdateStatus(item.order_id, "DISPATCHED")}
                    >
                      <Text style={styles.progressBtnText}>Dispatch Order &rarr;</Text>
                    </TouchableOpacity>
                  )}

                  {!isPending && orderStatus === "DISPATCHED" && (
                    <TouchableOpacity
                      style={[styles.progressBtn, { backgroundColor: Colors.secondary }]}
                      onPress={() => handleUpdateStatus(item.order_id, "DELIVERED")}
                    >
                      <Text style={styles.progressBtnText}>Mark Delivered ✓</Text>
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
  tabBar: {
    flexDirection: "row",
    backgroundColor: "#ffffff",
    borderBottomWidth: 1,
    borderBottomColor: Colors.border
  },
  tabItem: {
    flex: 1,
    paddingVertical: 12,
    alignItems: "center"
  },
  tabItemActive: {
    borderBottomWidth: 3,
    borderBottomColor: Colors.primary
  },
  tabText: {
    fontSize: 12,
    fontWeight: "700",
    color: Colors.textSecondary
  },
  tabTextActive: {
    color: Colors.primary
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
    fontSize: 16,
    fontWeight: "700",
    color: Colors.text
  },
  emptySubtitle: {
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
  cardHeader: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "flex-start"
  },
  orderTitle: {
    fontSize: 16,
    fontWeight: "800",
    color: Colors.text
  },
  customerName: {
    fontSize: 13,
    color: Colors.textSecondary,
    marginTop: 2
  },
  statusBadge: {
    backgroundColor: "#eff6ff",
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 6
  },
  statusBadgeText: {
    fontSize: 10,
    fontWeight: "800",
    color: Colors.primaryDark
  },
  addressText: {
    fontSize: 12,
    color: Colors.text,
    marginTop: 6
  },
  itemsBox: {
    backgroundColor: "#f8fafc",
    padding: 10,
    borderRadius: 8,
    marginVertical: 10
  },
  itemsTitle: {
    fontSize: 11,
    fontWeight: "700",
    color: Colors.textSecondary,
    marginBottom: 4
  },
  itemRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    paddingVertical: 2
  },
  itemName: {
    fontSize: 13,
    color: Colors.text,
    fontWeight: "600"
  },
  itemUnavailable: {
    color: "#94a3b8",
    textDecorationLine: "line-through"
  },
  itemPrice: {
    fontSize: 13,
    fontWeight: "700",
    color: Colors.text
  },
  footerRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    paddingTop: 8,
    borderTopWidth: 1,
    borderTopColor: "#f1f5f9"
  },
  amountLabel: {
    fontSize: 11,
    color: Colors.textSecondary
  },
  amountVal: {
    fontSize: 18,
    fontWeight: "800",
    color: Colors.primaryDark
  },
  actionBtnRow: {
    flexDirection: "row",
    gap: 8
  },
  rejectBtn: {
    backgroundColor: "#fee2e2",
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 6
  },
  rejectBtnText: {
    color: Colors.danger,
    fontWeight: "700",
    fontSize: 12
  },
  confirmBtn: {
    backgroundColor: Colors.secondary,
    paddingHorizontal: 14,
    paddingVertical: 8,
    borderRadius: 6
  },
  confirmBtnText: {
    color: "#ffffff",
    fontWeight: "700",
    fontSize: 12
  },
  progressBtn: {
    backgroundColor: Colors.primary,
    paddingHorizontal: 14,
    paddingVertical: 8,
    borderRadius: 6
  },
  progressBtnText: {
    color: "#ffffff",
    fontWeight: "700",
    fontSize: 12
  }
});
